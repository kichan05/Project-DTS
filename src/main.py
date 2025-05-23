from dotenv import load_dotenv
import os
import time
import flet as ft
from flet.core.file_picker import FilePickerFile
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

client = OpenAI(api_key=OPENAI_API_KEY)

def upload_file(files : list[FilePickerFile]) :
    result_files = []

    for file in files:
        f = open(file.path, "rb")
        res = client.files.create(file=f, purpose="user_data")
        result_files.append(res)

    return result_files



def main(page: ft.Page):
    page.title = "자동 TTS"
    selected_file_list : list[FilePickerFile] = []
    def pick_files_result(e : ft.FilePickerResultEvent):
        selected_file_list.extend(e.files)
        refresh_file_list()

    def refresh_file_list():
        file_list.controls.clear()

        for n, file in enumerate(selected_file_list):
            file_list.controls.append(
                ft.Row([
                    ft.Text(f"{n} - {file.name}"),
                    ft.IconButton(ft.Icons.DELETE, on_click=lambda _, p = file.path: delete_file(p))
                ])
            )

        page.update()

    def delete_file(path):
        selected_file_list[:] = list(filter(lambda x: x.path != path, selected_file_list))
        refresh_file_list()

    def on_upload_click(e):
        loading_view.visible = True
        page.update()

        upload_file(selected_file_list)

        loading_view.visible = False
        page.update()

    loading_view = ft.Text("업로드 중", visible=False)
    pick_files_dialog = ft.FilePicker(on_result=pick_files_result)
    page.overlay.append(pick_files_dialog)

    file_list = ft.Column()

    page.add(
        ft.Column(
            [
                ft.ElevatedButton(
                    "파일 선택",
                    icon = ft.Icons.FILE_OPEN,
                    on_click=lambda _ : pick_files_dialog.pick_files(
                        allow_multiple=True
                    )
                ),
                file_list,
                ft.Row([
                    ft.ElevatedButton(
                        "파일 업로드",
                        icon=ft.Icons.UPLOAD_FILE,
                        on_click=on_upload_click
                    ),
                    loading_view,
                ])
            ]
        )
    )


ft.app(main)
