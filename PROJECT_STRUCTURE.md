# ChatGPT Mock - Project Structure

## 📁 Directory Structure

```
ChatGPTMock/
├── 📁 config/          # Configuration files (model_config.ini, .env, etc.)
├── 📁 database/        # Database files and migration scripts
├── 📁 deployment/      # Deployment scripts and configurations
├── 📁 docs/           # Documentation and guides
├── 📁 scripts/        # Utility and maintenance scripts
├── 📁 static/         # Static assets (CSS, images, JS)
├── 📁 templates/      # HTML templates
├── 📁 tests/          # Test files
├── 📁 archive/        # Archived files
├── app_flask.py       # Main Flask application
├── openai_assistant_manager.py  # OpenAI integration
├── startup.py         # Application startup
├── requirements.txt   # Python dependencies
└── pyproject.toml     # Project metadata
```

## 🚀 Quick Start

1. Install dependencies: `pip install -r requirements.txt`
2. Configure your API key in `config/model_config.ini`
3. Run the application: `python app_flask.py`

## 📝 Key Files

- **app_flask.py** - Main Flask web application
- **config/model_config.ini** - AI model configuration (can be edited without restart)
- **openai_assistant_manager.py** - OpenAI API integration and conversation management

## 🔧 Configuration

All configuration files are located in the `config/` directory. The main configuration file is `model_config.ini` which controls:

- AI model selection and behavior
- Web search keywords and triggers
- Response formatting guidelines
- API keys and settings

## 📚 Documentation

All documentation files are located in the `docs/` directory including setup guides, troubleshooting, and configuration documentation.