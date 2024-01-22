# Anime/Serien Scraper

Anime/Serien Scraper is a versatile tool designed for downloading all seasons and episodes of anime from Aniworld.to and series from S.to. It provides an easy-to-use interface for selecting and downloading content directly to your machine.

## Features

- Download entire seasons or individual episodes.
- Supports two popular hosting services: Aniworld for anime and SerienStream for series.
- User-friendly web interface for easy navigation and downloads.

## Prerequisites

Before you begin, ensure you have the following installed:
- Python 3.x
- [ffmpeg](https://ffmpeg.org) - This should be installed in the root directory of the GitHub repository.

## Installation

1. **Clone the Repository**:
   ```
   git clone [repository URL]
   ```
2. **Install Dependencies**:
   Navigate to the root directory of the cloned repository and run:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. **Launch the Application**:
   In your terminal or command prompt, navigate to the root directory of the cloned repository and run:
   ```
   python app.py
   ```
   This command starts the Flask server hosting the application.

2. **Accessing the Application**:
   - **Localhost**: Visit `http://localhost:5000` in your web browser.
   - **Local Network**: Access the application from another device on the same network via `http://[Your-IP-Address]:5000`.


## Troubleshooting & Support

- Ensure all dependencies are correctly installed and configured.
- Check that ffmpeg is placed in the correct directory.
- If you encounter issues or have suggestions, please open an issue or submit a pull request on GitHub.

## Contributing

Contributions to the Anime/Serien Scraper are welcome! If you have suggestions for improvement or want to contribute to the code, please feel free to create a pull request or open an issue.

## License

This project is licensed under the [MIT License](LICENSE).

---

This README provides a basic overview. For more detailed instructions and information, refer to the individual documentation files and comments within the codebase.