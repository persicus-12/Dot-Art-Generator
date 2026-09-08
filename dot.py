


import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image


R_SCALE = 0.2126
G_SCALE = 0.7152
B_SCALE = 0.0722

DOT_TO_HEX = [
    0x01, 0x08, 0x02, 0x10,
    0x04, 0x20, 0x40, 0x80
]

ORDERED_DITHER_MATRIX = [
    0, 128, 192, 64,
    48, 176, 240, 112,
    32, 160, 224, 96,
    16, 144, 208, 80
]

DITHER_NONE = "None"
DITHER_ORDERED = "Ordered"
DITHER_ATKINSON = "Atkinson"
DITHER_FS = "Floyd-Steinberg"


def create_graymap(image):
    image = image.convert("RGBA")
    width, height = image.size

    graymap = []

    for y in range(height):
        for x in range(width):
            r, g, b, a = image.getpixel((x, y))

            if a < 255:
                gray = 255
            else:
                gray = (
                    r * R_SCALE +
                    g * G_SCALE +
                    b * B_SCALE
                )

            graymap.append(gray)

    return graymap, width, height


def prepare_image(image, output_width):
    original_width, original_height = image.size

    if original_width == 0 or original_height == 0:
        raise ValueError("Invalid image dimensions.")

    char_aspect_ratio = 0.5

    output_height = int(
        (original_height / original_width)
        * output_width
        * char_aspect_ratio
    )

    output_height = max(1, output_height)

    pixel_width = output_width * 2
    pixel_height = output_height * 4

    return image.resize(
        (pixel_width, pixel_height),
        Image.Resampling.LANCZOS
    )


def atkinson_dither(graymap, width, height, threshold):
    data = graymap.copy()

    for y in range(height):
        for x in range(width):
            index = y * width + x

            old_pixel = data[index]
            target = 255 if old_pixel > threshold else 0
            error = old_pixel - target

            data[index] = target

            error_part = error / 8

            positions = [
                (x + 1, y),
                (x + 2, y),
                (x - 1, y + 1),
                (x, y + 1),
                (x + 1, y + 1),
                (x, y + 2)
            ]

            for nx, ny in positions:
                if 0 <= nx < width and 0 <= ny < height:
                    neighbor = ny * width + nx
                    data[neighbor] += error_part

    return data


def floyd_steinberg_dither(graymap, width, height, threshold):
    data = graymap.copy()

    for y in range(height):
        for x in range(width):
            index = y * width + x

            old_pixel = data[index]
            new_pixel = 255 if old_pixel > threshold else 0

            error = old_pixel - new_pixel

            data[index] = new_pixel

            if x + 1 < width:
                data[index + 1] += error * 7 / 16

            if x - 1 >= 0 and y + 1 < height:
                data[index + width - 1] += error * 3 / 16

            if y + 1 < height:
                data[index + width] += error * 5 / 16

            if x + 1 < width and y + 1 < height:
                data[index + width + 1] += error * 1 / 16

    return data


def ordered_threshold(x, y, threshold):
    index = (y % 4) * 4 + (x % 4)

    return (
        threshold
        + ORDERED_DITHER_MATRIX[index]
        - 127
    )


def graymap_to_braille(
    graymap,
    width,
    height,
    threshold,
    dither,
    black_on_white
):
    if dither == DITHER_ATKINSON:
        processed = atkinson_dither(
            graymap,
            width,
            height,
            threshold
        )

    elif dither == DITHER_FS:
        processed = floyd_steinberg_dither(
            graymap,
            width,
            height,
            threshold
        )

    else:
        processed = graymap.copy()

    cell_width = width // 2
    cell_height = height // 4

    result = []

    for cell_y in range(cell_height):
        line = []

        for cell_x in range(cell_width):
            character = 0x2800

            for pip in range(8):
                pixel_x = cell_x * 2 + pip % 2
                pixel_y = cell_y * 4 + pip // 2

                pixel_index = pixel_y * width + pixel_x
                gray = processed[pixel_index]

                if dither == DITHER_ORDERED:
                    local_threshold = ordered_threshold(
                        pixel_x,
                        pixel_y,
                        threshold
                    )
                else:
                    local_threshold = threshold

                if black_on_white:
                    make_dot = gray < local_threshold
                else:
                    make_dot = gray > local_threshold

                if make_dot:
                    character += DOT_TO_HEX[pip]

            line.append(chr(character))

        result.append("".join(line))

    return "\n".join(result)


def simple_character_art(
    graymap,
    width,
    height,
    black_on_white
):
    characters = [
        "⠀",
        "⠁",
        "⠃",
        "⠇",
        "⠏",
        "⠟",
        "⠿",
        "⣿"
    ]

    result = []

    for y in range(height):
        line = []

        for x in range(width):
            gray = graymap[y * width + x]

            value = (
                gray
                if black_on_white
                else 255 - gray
            )

            index = int(
                value / 256 * len(characters)
            )

            index = min(
                index,
                len(characters) - 1
            )

            line.append(characters[index])

        result.append("".join(line))

    return "\n".join(result)


def optimize_for_chat(
    text,
    code_block=True
):
    lines = text.splitlines()

    lines = [
        line.rstrip()
        for line in lines
    ]

    while lines and not lines[0]:
        lines.pop(0)

    while lines and not lines[-1]:
        lines.pop()

    text = "\n".join(lines)

    if code_block:
        text = "```text\n" + text + "\n```"

    return text


def generate_dot_art(
    image_path,
    output_width,
    threshold,
    dither,
    black_on_white,
    mode
):
    image = Image.open(image_path)

    image = prepare_image(
        image,
        output_width
    )

    graymap, width, height = create_graymap(image)

    if mode == "Simple":
        return simple_character_art(
            graymap,
            width,
            height,
            black_on_white
        )

    return graymap_to_braille(
        graymap,
        width,
        height,
        threshold,
        dither,
        black_on_white
    )


class DotArtApp:

    def __init__(self, root):
        self.root = root

        self.root.title(
            "Dot Art Generator"
        )

        self.root.geometry(
            "1200x800"
        )

        self.root.minsize(
            900,
            600
        )

        self.image_path = None
        self.generated_art = ""

        self.create_controls()
        self.create_output()

    def create_controls(self):
        frame = tk.Frame(
            self.root,
            padx=10,
            pady=10
        )

        frame.pack(fill="x")

        tk.Button(
            frame,
            text="Browse Image",
            command=self.browse_image,
            width=15
        ).grid(
            row=0,
            column=0,
            padx=5
        )

        self.file_label = tk.Label(
            frame,
            text="No image selected",
            anchor="w"
        )

        self.file_label.grid(
            row=0,
            column=1,
            columnspan=6,
            sticky="we",
            padx=5
        )

        tk.Label(
            frame,
            text="Width:"
        ).grid(
            row=1,
            column=0,
            sticky="e"
        )

        self.width_var = tk.IntVar(
            value=100
        )

        tk.Spinbox(
            frame,
            from_=20,
            to=300,
            textvariable=self.width_var,
            width=8
        ).grid(
            row=1,
            column=1,
            sticky="w"
        )

        tk.Label(
            frame,
            text="Threshold:"
        ).grid(
            row=1,
            column=2,
            sticky="e"
        )

        self.threshold_var = tk.IntVar(
            value=128
        )

        tk.Scale(
            frame,
            from_=0,
            to=255,
            orient="horizontal",
            variable=self.threshold_var,
            length=180
        ).grid(
            row=1,
            column=3
        )

        tk.Label(
            frame,
            text="Dithering:"
        ).grid(
            row=1,
            column=4,
            sticky="e"
        )

        self.dither_var = tk.StringVar(
            value=DITHER_ATKINSON
        )

        tk.OptionMenu(
            frame,
            self.dither_var,
            DITHER_NONE,
            DITHER_ORDERED,
            DITHER_ATKINSON,
            DITHER_FS
        ).grid(
            row=1,
            column=5
        )

        tk.Label(
            frame,
            text="Mode:"
        ).grid(
            row=2,
            column=0,
            sticky="e"
        )

        self.mode_var = tk.StringVar(
            value="Braille"
        )

        tk.OptionMenu(
            frame,
            self.mode_var,
            "Braille",
            "Simple"
        ).grid(
            row=2,
            column=1,
            sticky="w"
        )

        self.black_on_white_var = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            frame,
            text="Black on White",
            variable=self.black_on_white_var
        ).grid(
            row=2,
            column=2,
            columnspan=2,
            sticky="w"
        )

        self.chat_mode_var = tk.BooleanVar(
            value=False
        )

        tk.Checkbutton(
            frame,
            text="Chat Mode",
            variable=self.chat_mode_var
        ).grid(
            row=2,
            column=4,
            sticky="w"
        )

        self.code_block_var = tk.BooleanVar(
            value=True
        )

        tk.Checkbutton(
            frame,
            text="Code Block",
            variable=self.code_block_var
        ).grid(
            row=2,
            column=5,
            sticky="w"
        )

        tk.Button(
            frame,
            text="GENERATE",
            command=self.generate,
            width=15
        ).grid(
            row=3,
            column=5,
            padx=5,
            pady=5
        )

    def create_output(self):
        frame = tk.Frame(
            self.root,
            padx=10,
            pady=5
        )

        frame.pack(
            fill="both",
            expand=True
        )

        self.text = tk.Text(
            frame,
            wrap="none",
            font=("Consolas", 10),
            bg="black",
            fg="white",
            insertbackground="white"
        )

        self.text.pack(
            side="left",
            fill="both",
            expand=True
        )

        scrollbar_y = tk.Scrollbar(
            frame,
            orient="vertical",
            command=self.text.yview
        )

        scrollbar_y.pack(
            side="right",
            fill="y"
        )

        scrollbar_x = tk.Scrollbar(
            self.root,
            orient="horizontal",
            command=self.text.xview
        )

        scrollbar_x.pack(fill="x")

        self.text.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set
        )

        bottom = tk.Frame(
            self.root,
            pady=10
        )

        bottom.pack(fill="x")

        tk.Button(
            bottom,
            text="Copy",
            command=self.copy_to_clipboard,
            width=18
        ).pack(
            side="left",
            padx=10
        )

        tk.Button(
            bottom,
            text="Copy for Telegram",
            command=self.copy_for_telegram,
            width=20
        ).pack(
            side="left"
        )

        tk.Button(
            bottom,
            text="Save TXT",
            command=self.save_txt,
            width=18
        ).pack(
            side="left",
            padx=10
        )

    def browse_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                (
                    "Image files",
                    "*.jpg *.jpeg *.png *.bmp *.webp *.gif"
                ),
                ("All files", "*.*")
            ]
        )

        if path:
            self.image_path = path
            self.file_label.config(text=path)

    def generate(self):
        if not self.image_path:
            messagebox.showwarning(
                "No Image",
                "Please select an image first."
            )
            return

        try:
            self.root.config(cursor="wait")
            self.root.update()

            self.generated_art = generate_dot_art(
                self.image_path,
                self.width_var.get(),
                self.threshold_var.get(),
                self.dither_var.get(),
                self.black_on_white_var.get(),
                self.mode_var.get()
            )

            self.display_art(self.generated_art)

        except Exception as error:
            messagebox.showerror(
                "Error",
                str(error)
            )

        finally:
            self.root.config(cursor="")

    def display_art(self, art):
        self.text.delete(
            "1.0",
            tk.END
        )

        self.text.insert(
            "1.0",
            art
        )

    def copy_to_clipboard(self):
        if not self.generated_art:
            return

        self.root.clipboard_clear()

        self.root.clipboard_append(
            self.generated_art
        )

        self.root.update()

    def copy_for_telegram(self):
        if not self.generated_art:
            return

        optimized = optimize_for_chat(
            self.generated_art,
            self.code_block_var.get()
        )

        self.root.clipboard_clear()

        self.root.clipboard_append(
            optimized
        )

        self.root.update()

        messagebox.showinfo(
            "Copied",
            "Optimized text copied for Telegram."
        )

    def save_txt(self):
        if not self.generated_art:
            return

        path = filedialog.asksaveasfilename(
            title="Save Dot Art",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("All files", "*.*")
            ]
        )

        if not path:
            return

        with open(
            path,
            "w",
            encoding="utf-8"
        ) as file:
            file.write(
                self.generated_art
            )

        messagebox.showinfo(
            "Saved",
            f"Saved successfully:\n{path}"
        )


if __name__ == "__main__":
    root = tk.Tk()
    app = DotArtApp(root)
    root.mainloop()