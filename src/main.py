from dotenv import load_dotenv
import os
import time
import flet as ft
from flet.core.file_picker import FilePickerFile

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

def main(page: ft.Page):
    page.title = "자동 TTS"

    selected_file_list : list[FilePickerFile] = []

    def pick_files_result(e : ft.FilePickerResultEvent):
        selected_file_list.extend(e.files)
        refresh_file_list()

    def refresh_file_list():
        file_list.controls.clear()

        for file in selected_file_list:
            file_list.controls.append(
                ft.Row([
                    ft.Text(file.path),
                    ft.IconButton(ft.Icons.DELETE, on_click=lambda _, p = file.path: delete_file(p))
                ])
            )

        page.update()

    def delete_file(path):
        selected_file_list[:] = list(filter(lambda x: x.path != path, selected_file_list))
        refresh_file_list()

    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    file_list = ft.Column()

    page.add(
        ft.Column(
            [
                ft.ElevatedButton(
                    "Pick files",
                    icon = ft.Icons.UPLOAD_FILE,
                    on_click=lambda _ : pick_files_dialog.pick_files(
                        allow_multiple=True
                    )
                ),
                file_list
            ]
        )
    )


ft.app(main)
