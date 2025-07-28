import os
import re
import shutil
from pathlib import Path

import bpy


class OBJECT_OT_interpolate_bake(bpy.types.Operator):
    """Convert simulation caches to stepped interpolation on N frames"""

    bl_idname = "object.interpolate_bake"
    bl_label = "Interpolate Simulation Caches on N Frames"
    bl_options = {"REGISTER", "UNDO"}

    step: bpy.props.IntProperty(
        name="Step Interval",
        default=2,
        min=1,
        max=24,
        description="Number of frames to step (e.g. 2 = on 2s, 3 = on 3s)",
    )

    backup_original: bpy.props.BoolProperty(
        name="Create Backup",
        default=True,
        description="Create backup of original cache files before modification",
    )

    cache_types: bpy.props.EnumProperty(
        name="Cache Types",
        description="Which cache types to process",
        items=[
            ("CLOTH", "Cloth", "Process cloth (.bphys) caches"),
        ],
        default="CLOTH",
    )

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "step")
        layout.prop(self, "cache_types")
        layout.prop(self, "backup_original")

    def execute(self, context):
        try:
            return self.process_caches(context)
        except Exception as e:
            self.report({"ERROR"}, f"Unexpected error: {str(e)}")
            return {"CANCELLED"}

    def process_caches(self, context):
        step = self.step
        blend_file_path = bpy.data.filepath

        if not blend_file_path:
            self.report(
                {"ERROR"}, "Please save your blend file before running this script."
            )
            return {"CANCELLED"}

        # Find all possible cache directories
        cache_dirs = self.find_cache_directories(blend_file_path)

        if not cache_dirs:
            self.report({"ERROR"}, "No cache directories found.")
            return {"CANCELLED"}

        total_processed = 0
        processed_dirs = []

        for cache_dir in cache_dirs:
            try:
                processed_count = self.process_cache_directory(cache_dir, step)
                if processed_count > 0:
                    total_processed += processed_count
                    processed_dirs.append(os.path.basename(cache_dir))
            except Exception as e:
                self.report({"WARNING"}, f"Error processing {cache_dir}: {str(e)}")
                continue

        if total_processed > 0:
            dirs_str = ", ".join(processed_dirs)
            self.report(
                {"INFO"},
                f"Applied stepped interpolation every {step} frame(s) to {total_processed} files in: {dirs_str}",
            )
        else:
            self.report(
                {"WARNING"},
                "No cache files were processed. Check if caches exist and are accessible.",
            )

        return {"FINISHED"}

    def find_cache_directories(self, blend_file_path):
        """Find all possible cache directories for the blend file"""
        cache_dirs = []
        blend_dir = os.path.dirname(blend_file_path)
        blend_name = os.path.splitext(os.path.basename(blend_file_path))[0]

        # Standard cache directory naming patterns
        cache_patterns = [
            f"blendcache_{blend_name}",  # Standard naming
            "blendcache",  # Generic naming
            "cache",  # Simple naming
        ]

        # Check for cache directories
        for pattern in cache_patterns:
            cache_path = os.path.join(blend_dir, pattern)
            if os.path.exists(cache_path) and os.path.isdir(cache_path):
                cache_dirs.append(cache_path)

        # Also check for cache directories in subdirectories
        try:
            for item in os.listdir(blend_dir):
                item_path = os.path.join(blend_dir, item)
                if os.path.isdir(item_path) and "cache" in item.lower():
                    if item_path not in cache_dirs:
                        cache_dirs.append(item_path)
        except PermissionError:
            pass

        return cache_dirs

    def process_cache_directory(self, directory, step):
        """Process all cache files in a directory"""
        print(f"Processing cache directory: {directory}")

        if not os.path.exists(directory):
            return 0

        # Create backup if requested
        if self.backup_original:
            self.create_backup(directory)

        # Find all cache files and group them
        cache_groups = self.group_cache_files(directory)

        if not cache_groups:
            print(f"No cache files found in {directory}")
            return 0

        processed_count = 0

        for group_key, files in cache_groups.items():
            try:
                group_processed = self.process_cache_group(directory, files, step)
                processed_count += group_processed
                print(f"Processed {group_processed} files for cache group: {group_key}")
            except Exception as e:
                print(f"Error processing cache group {group_key}: {str(e)}")
                continue

        return processed_count

    def group_cache_files(self, directory):
        """Group cache files by type and identifier"""
        cache_groups = {}

        # Supported cache file extensions and their patterns
        cache_patterns = {
            ".bphys": r"(.+)_(\d{6})_(.+)\.bphys$",  # Cloth, soft body: prefix_frame_suffix.bphys
        }

        try:
            for filename in os.listdir(directory):
                file_path = os.path.join(directory, filename)
                if not os.path.isfile(file_path):
                    continue

                # Check each pattern
                for ext, pattern in cache_patterns.items():
                    if filename.endswith(ext):
                        # Skip if cache type filtering is active and doesn't match
                        if not self.should_process_cache_type(ext):
                            continue

                        match = re.match(pattern, filename)
                        if match:
                            if ext == ".bphys":
                                prefix, frame_str, suffix = match.groups()
                                group_key = f"{prefix}_{suffix}{ext}"
                            else:
                                prefix, frame_str = match.groups()
                                group_key = f"{prefix}{ext}"

                            frame_num = int(frame_str)

                            if group_key not in cache_groups:
                                cache_groups[group_key] = []

                            cache_groups[group_key].append((filename, frame_num))
                            break

        except PermissionError as e:
            print(f"Permission error accessing directory {directory}: {str(e)}")
        except Exception as e:
            print(f"Error grouping cache files in {directory}: {str(e)}")

        # Sort each group by frame number
        for group_key in cache_groups:
            cache_groups[group_key].sort(key=lambda x: x[1])

        return cache_groups

    def should_process_cache_type(self, extension):
        """Check if this cache type should be processed based on user selection"""
        if self.cache_types == "ALL":
            return True
        elif self.cache_types == "CLOTH" and extension == ".bphys":
            return True
        return False

    def process_cache_group(self, directory, files, step):
        """Process a group of cache files with the same identifier"""
        processed_count = 0

        # Create a lookup dictionary for existing frames
        frame_lookup = {frame_num: filename for filename, frame_num in files}
        frame_numbers = sorted(frame_lookup.keys())

        if not frame_numbers:
            return 0

        min_frame = frame_numbers[0]
        max_frame = frame_numbers[-1]

        # Process each frame that should be stepped
        for current_frame in range(min_frame, max_frame + 1):
            if current_frame not in frame_lookup:
                continue

            # If this frame is not on a step boundary, replace it
            if current_frame % step != min_frame % step:
                # Find the previous step frame
                step_offset = (current_frame - min_frame) % step
                prev_step_frame = current_frame - step_offset

                if prev_step_frame in frame_lookup:
                    try:
                        source_path = os.path.join(
                            directory, frame_lookup[prev_step_frame]
                        )
                        target_path = os.path.join(
                            directory, frame_lookup[current_frame]
                        )

                        # Copy the step frame data to current frame
                        if os.path.exists(source_path):
                            shutil.copy2(source_path, target_path)
                            processed_count += 1
                    except Exception as e:
                        print(f"Error copying {source_path} to {target_path}: {str(e)}")

        return processed_count

    def create_backup(self, directory):
        """Create a backup of the cache directory"""
        try:
            backup_dir = f"{directory}_backup"
            counter = 1

            # Find a unique backup directory name
            while os.path.exists(backup_dir):
                backup_dir = f"{directory}_backup_{counter}"
                counter += 1

            shutil.copytree(directory, backup_dir)
            print(f"Created backup at: {backup_dir}")

        except Exception as e:
            print(f"Warning: Could not create backup: {str(e)}")


# UI Integration
def draw_cloth_func(self, context):
    layout = self.layout
    layout.separator()
    layout.operator(
        "object.interpolate_bake",
        text="Interpolate Cache with Step Interval",
        icon="FCURVE",
    )
