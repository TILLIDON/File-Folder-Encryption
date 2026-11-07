# Folder & File Security Tool

A secure, lightweight desktop utility built in Python with a clean graphical user interface (GUI) to encrypt and decrypt individual files or entire directories using **AES-256-GCM** authenticated encryption.

## Features
- **AES-256-GCM Encryption**: High-security cryptographic standard providing both confidentiality and integrity protection.
- **Password Protection**: Enforces a minimum 12-character password length with confirmation prompts.
- **Batch Processing**: Secure entire folder structures recursively or protect single files individually.
- **Dark-Themed GUI**: Built using `tkinter` with a custom modern minimalist dark layout.

---

## Prerequisites
Make sure you have **Python 3.x** installed on your system.

## Installation

1. Clone or download this repository.
2. Install the required Python cryptography library via terminal or command prompt:
   ```bash
   pip install cryptography