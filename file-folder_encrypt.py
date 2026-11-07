
import os
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from pathlib import Path
import secrets

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.exceptions import InvalidTag

MAGIC = b"FLOCK1"
SALT_SIZE = 16
NONCE_SIZE = 12
ITERATIONS = 600_000


def derive_key(password, salt):
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=ITERATIONS
    )
    return kdf.derive(password.encode("utf-8"))


def encrypt_file(source, password):
    source = Path(source)
    destination = Path(str(source) + ".locked")

    if destination.exists():
        return False

    salt = secrets.token_bytes(SALT_SIZE)
    nonce = secrets.token_bytes(NONCE_SIZE)
    key = derive_key(password, salt)

    encrypted = AESGCM(key).encrypt(
        nonce, source.read_bytes(), MAGIC
    )

    temp = Path(str(destination) + ".tmp")

    try:
        temp.write_bytes(MAGIC + salt + nonce + encrypted)
        os.replace(temp, destination)
        source.unlink()
        return True
    finally:
        if temp.exists():
            temp.unlink()


def decrypt_file(source, password):
    source = Path(source)

    if not source.name.endswith(".locked"):
        return False

    destination = Path(str(source)[:-7])

    if destination.exists():
        return False

    temp = Path(str(destination) + ".tmp")

    try:
        data = source.read_bytes()

        if len(data) < 50 or not data.startswith(MAGIC):
            raise ValueError("Invalid encrypted file.")

        salt = data[6:22]
        nonce = data[22:34]
        encrypted = data[34:]

        key = derive_key(password, salt)

        decrypted = AESGCM(key).decrypt(
            nonce, encrypted, MAGIC
        )

        temp.write_bytes(decrypted)
        os.replace(temp, destination)
        source.unlink()

        return True

    finally:
        if temp.exists():
            temp.unlink()


def get_password(confirm=False):
    password = simpledialog.askstring(
        "Password",
        "Enter password:",
        show="*"
    )

    if password is None:
        return None

    if len(password) < 12:
        messagebox.showwarning(
            "Weak Password",
            "Password must contain at least 12 characters."
        )
        return None

    if confirm:
        second = simpledialog.askstring(
            "Confirm Password",
            "Re-enter password:",
            show="*"
        )

        if second is None:
            return None

        if password != second:
            messagebox.showerror(
                "Error", "Passwords do not match."
            )
            return None

    return password


def select_and_process_file(mode):
    if mode == "lock":
        file = filedialog.askopenfilename(
            title="Select File to Encrypt"
        )
    else:
        file = filedialog.askopenfilename(
            title="Select Encrypted File",
            filetypes=[("Locked files", "*.locked")]
        )

    if not file:
        return

    password = get_password(confirm=(mode == "lock"))

    if password is None:
        return

    try:
        if mode == "lock":
            result = encrypt_file(file, password)
        else:
            result = decrypt_file(file, password)

        if result:
            messagebox.showinfo(
                "Success",
                "File encrypted successfully!"
                if mode == "lock"
                else "File decrypted successfully!"
            )
        else:
            messagebox.showwarning(
                "Not Processed",
                "File already exists, is invalid, or cannot be processed."
            )

    except InvalidTag:
        messagebox.showerror(
            "Authentication Failed",
            "Incorrect password or damaged encrypted file."
        )

    except Exception as error:
        messagebox.showerror("Error", str(error))


def process_folder(folder, password, mode):
    files = []

    for root, dirs, filenames in os.walk(folder):
        dirs[:] = [
            d for d in dirs
            if not (Path(root) / d).is_symlink()
        ]

        for filename in filenames:
            path = Path(root) / filename

            if path.is_symlink():
                continue

            if mode == "lock" and not filename.endswith(".locked"):
                files.append(path)

            elif mode == "unlock" and filename.endswith(".locked"):
                files.append(path)

    success = 0
    failed = 0

    for path in files:
        try:
            result = (
                encrypt_file(path, password)
                if mode == "lock"
                else decrypt_file(path, password)
            )

            if result:
                success += 1
            else:
                failed += 1

        except Exception:
            failed += 1

    return success, failed


def select_and_process_folder(mode):
    folder = filedialog.askdirectory(
        title="Select Folder"
    )

    if not folder:
        return

    password = get_password(confirm=(mode == "lock"))

    if password is None:
        return

    try:
        success, failed = process_folder(
            folder, password, mode
        )

        messagebox.showinfo(
            "Operation Complete",
            f"Successfully processed: {success}\n"
            f"Skipped/failed: {failed}"
        )

    except Exception as error:
        messagebox.showerror("Error", str(error))


# GUI

root = tk.Tk()
root.title("Folder & File Security")
root.geometry("460x480")
root.resizable(False, False)
root.configure(bg="#151922")

tk.Label(
    root,
    text="FOLDER SECURITY",
    font=("Segoe UI", 22, "bold"),
    fg="white",
    bg="#151922"
).pack(pady=(25, 5))

tk.Label(
    root,
    text="AES-256-GCM Encryption System",
    font=("Segoe UI", 10),
    fg="#aab3c5",
    bg="#151922"
).pack(pady=5)


def add_button(text, command, color):
    tk.Button(
        root,
        text=text,
        command=command,
        font=("Segoe UI", 11, "bold"),
        bg=color,
        fg="white",
        activeforeground="white",
        relief="flat",
        width=29,
        height=2,
        cursor="hand2"
    ).pack(pady=7)


add_button(
    "LOCK FILE",
    lambda: select_and_process_file("lock"),
    "#246bce"
)

add_button(
    "UNLOCK FILE",
    lambda: select_and_process_file("unlock"),
    "#21875a"
)

add_button(
    "LOCK FOLDER",
    lambda: select_and_process_folder("lock"),
    "#246bce"
)

add_button(
    "UNLOCK FOLDER",
    lambda: select_and_process_folder("unlock"),
    "#21875a"
)

tk.Label(
    root,
    text="Keep your password safe. No recovery available.",
    font=("Segoe UI", 9),
    fg="#aab3c5",
    bg="#151922"
).pack(side="bottom", pady=20)

root.mainloop()
