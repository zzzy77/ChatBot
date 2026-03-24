First, install Miniconda on your computer.  
Link: [https://www.anaconda.com/download/success?reg=skipped](https://www.anaconda.com/download/success?reg=skipped)

Then, open **Command Prompt (CMD)** or **PowerShell** and run:

```bash
conda config --set channel_priority flexible
conda env create -f environment.yml -n your_env_name
conda activate your_env_name
streamlit run chatbot.py
```
After the environment is successfully created, it is recommended to restore the default channel priority setting to avoid unintended mixing of packages from different channels in future installations:

```bash
conda config --set channel_priority strict
```
