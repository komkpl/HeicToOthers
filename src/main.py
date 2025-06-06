import flet as ft
from PIL import Image
import pillow_heif
import os
from pathlib import Path
import subprocess
import platform

def make_output_path(input_path: Path, output_extention: str) -> Path:
    return Path(os.path.splitext(input_path)[0] + "." + output_extention)

def convert_heic_to_others(input_path: Path, output_extention: str) -> Path:
    heif_file = pillow_heif.read_heif(input_path)
    image = Image.frombytes(
        heif_file.mode,
        heif_file.size,
        heif_file.data,
        "raw",
    )

    output_path = make_output_path(input_path, output_extention)
    image.save(output_path)
    print(f"変換完了: {output_path}")
    return output_path

def open_file(path: Path):
    path = path.parent
    try:
        if platform.system() == "Windows":
            os.startfile(path)
        elif platform.system() == "Darwin": # macOS
            subprocess.call(["open", path])
        else: # Linux
            subprocess.call(["xdg-open", path])
    except Exception as e:
        print(f"Error opening file: {path} -> {e}")

def main(page: ft.Page):
    page.title = "HEIC File Converter"
    selected_paths: list[str] = []

    progress_bar = ft.ProgressBar(width=400, value=0)
    progress_text = ft.Text(value="Progress: 0 / 0")
    selected_files = ft.Text()
    converted_files = ft.Column(
        controls=[ft.Text("No history", italic=True, color=ft.Colors.GREY)],
        spacing=5, 
        scroll=ft.ScrollMode.AUTO,
        )
    selected_files.value = "No files are selected"

    extensions = [
        "jpg",
        "png",
        "gif",
        "tiff",
    ]
    selected_extension = ft.Ref[ft.Dropdown]()

    snackbar = ft.SnackBar(
        content=ft.Text("No files are selected"),
        bgcolor=ft.Colors.TEAL_400,
        duration=2000, # ミリ秒
    )
    page.snack_bar = snackbar
    page.overlay.append(snackbar)

    page.update()

    def show_snackbar(message: str, bgcolor=ft.Colors.TEAL_400):
        snackbar.content = ft.Text(message)
        snackbar.bgcolor = bgcolor
        snackbar.open = True
        page.update()
    
    def pick_files_result(e: ft.FilePickerResultEvent):
        if not e.files:
            return
        
        selected_files.value = "\n".join(f.name for f in e.files)
        selected_paths.clear()
        selected_paths.extend(f.path for f in e.files)
        print(f"Selected files: {selected_files.value}")

        # 進捗バーの初期化
        progress_bar.value = 0
        progress_text.value = f"Progress: 0 / {len(selected_paths)}"
        page.update()

    
    # HEIC -> JPGに変換
    def convert_button_clicked(e):
        total = len(selected_paths)
        if total == 0:
            page.snack_bar = snackbar
            show_snackbar("No files are selected")
            page.update()
            return

        output_extention = selected_extension.current.value or "jpg"
        print(converted_files.controls[0])
        if isinstance(converted_files.controls[0], ft.Text) and "No history" == converted_files.controls[0].value:
            converted_files.controls.clear()
        for i, path in enumerate(selected_paths, start=1):
            try:
                output_path = convert_heic_to_others(path, output_extention)

                # TextButtonを作成して、変換されたファイルを開く
                btn = ft.TextButton(
                    text=str(output_path),
                    on_click=lambda e, p=output_path: open_file(p),
                    style=ft.ButtonStyle(color=ft.Colors.BLUE, overlay_color=ft.Colors.BLUE_100),
                )
                converted_files.controls.append(btn)

            except Exception as e:
                print(f"Conversion failed: {path} -> {e}")
                converted_files.controls.append(ft.Text(f"Conversion failed: {path} -> {e}", color=ft.Colors.RED))
                show_snackbar(f"Error converting {path}: {e}", bgcolor=ft.Colors.RED_400)
                page.update()
                return
            
            # 進捗更新
            progress_bar.value = i / total
            progress_text.value = f"Progress: {i} / {total}"
            page.update()
        
        progress_text.value += "✅ Done!"
        page.update()
    
    def get_extention_options():
        return [ft.dropdown.Option(ext) for ext in extensions]
    
    def clear_converted_files():
        converted_files.controls.clear()
        converted_files.controls.append(ft.Text("No history", italic=True, color=ft.Colors.GREY))

        progress_bar.value = 0
        progress_text.value = "Progress: 0 / 0"
        show_snackbar("History cleared successfully")
        page.update()
    
    # ファイルドロップ
    def on_drop(e: ft.DragTargetEvent):
        selected_files.value = ""
        selected_paths.clear()
        for file in e.files:
            selected_paths.append(file.path)
            selected_files.value += f"{Path(file.path).name}"
        page.update()
        print("Dropped files:", selected_paths)

    drop_target = ft.DragTarget(
        content=ft.Container(
            content=selected_files,
            width=400,
            height=200,
            border=ft.border.all(2, ft.colors.BLUE),
            border_radius=10,
            alignment=ft.alignment.center,
            padding=20,
            bgcolor=ft.Colors.BLUE_50,
        ),
        on_accept=on_drop,
    )
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    # UI配置
    page.add(
        ft.Column(
            [
                ft.Column(
                    [
                        ft.Row(
                        [
                            ft.ElevatedButton(
                                "Pick HEIC Files",
                                icon=ft.Icons.UPLOAD_FILE,
                                on_click=lambda _: pick_files_dialog.pick_files(
                                    allow_multiple=True,
                                    allowed_extensions=["heic", "HEIC"],
                                    dialog_title="Select HEIC files to convert",
                                ),
                            ),
                            selected_files,
                            ft.Container(expand=True),
                            ft.Dropdown(
                                ref=selected_extension,
                                label="Extension",
                                options=get_extention_options(),
                                value="jpg", # 初期値
                            ),
                        ],
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        ),
                        ft.ElevatedButton(
                            "Convert",
                            icon=ft.Icons.SAVE,
                            on_click=convert_button_clicked,
                        ),
                        converted_files,
                    ],
                    spacing=20,
                    expand=True,
                ),
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Row(
                                [
                                    progress_bar,
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE,
                                        tooltip="Clear History",
                                        on_click=lambda _: clear_converted_files(),
                                    ),
                                ], 
                                alignment=ft.MainAxisAlignment.CENTER,
                            ),
                            ft.Row([progress_text], alignment=ft.MainAxisAlignment.CENTER),
                        ],
                        spacing=5,
                    ),
                    padding=10,
                    alignment=ft.alignment.bottom_center,
                )
            ],
            spacing=20,
            expand=True,
        )
    )



ft.app(target=main)