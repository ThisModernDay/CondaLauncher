# CondaLauncher

![CondaLauncher Main Screen](https://github.com/thismodernday/CondaLauncher/raw/main/images/main_screen.png)

CondaLauncher is a Python application that allows you to manage and launch applications in different Conda environments.

![CondaLauncher Processes Modal](https://github.com/thismodernday/CondaLauncher/raw/main/images/processes_modal.png)

## Features

- List and manage applications with their associated Conda environments
- Launch applications in their respective Conda environments
- Monitor running processes and view their output
- Manage application configurations through a YAML file
- Edit the applications YAML file directly within the app

![CondaLauncher Manage Applications](https://github.com/thismodernday/CondaLauncher/raw/main/images/manage_applications.png)

## Prerequisites

- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution) installed on your system
- Python 3.10

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/thismodernday/CondaLauncher.git
   cd CondaLauncher
   ```

2. Create a new Conda environment:
   ```
   conda create -n conda-launcher python=3.10
   ```

3. Activate the environment:
   ```
   conda activate conda-launcher
   ```

4. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Configuration

1. The `applications.yaml` file in the project root directory contains the configuration for your applications.
2. You can edit this file directly in the CondaLauncher application by clicking the "Manage Applications" button.
3. Alternatively, you can edit the file manually. The format for each application is as follows:
   ```yaml
   applications:
     - name: "App Name"
       conda_env: "environment_name"
       path: "/path/to/your/app.py"
       description: "Brief description of the app"
   ```

## Usage

1. Ensure you're in the CondaLauncher directory and your conda-launcher environment is activated.

2. Run the application:
   ```
   python Launcher.py
   ```

3. Use the interface to select, launch, and manage your applications:
   - Select an application from the list to view its details
   - Click "Launch" to start the selected application
   - Click "Manage Applications" to edit the applications.yaml file within the app
   - Use "Ctrl+O" to open the Processes Modal and view running applications

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
