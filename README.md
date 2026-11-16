# AI Project Starter

This Python project predicts whether a support ticket is about an account, billing, or a technical issue. It trains a small naive Bayes classifier on labeled examples every time you run it. Everything runs locally using the Python standard library.

## Run it

Open a terminal in this repository. With Python 3.10 or later, run the following command.

```sh
python main.py "My invoice shows a duplicate charge"
```

Expected output is `billing`. Use `python3` if that is the Python command on your system. On Windows, if Python is installed under your user profile and `python` opens the Microsoft Store, you can call the installed executable directly. For a Python 3.13 installation, run this in PowerShell.

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe" main.py "My invoice shows a duplicate charge"
```

## Make it your own

1. Give the project a name and describe the problem you want it to solve.
2. Edit `examples.json` to add training examples or change the categories. Each example has `text` and `category` fields.
3. Try inputs outside the training examples and check the predictions. The demo uses 15 synthetic examples, so its predictions can be wrong. It prints `unknown` when the input shares no words with the training examples.

The `classify()` function in `main.py` is the starting point for changing how the app makes predictions.
