# InsightWell

A web application that allows students to journal their thoughts and emotions, with automatic emotion classification using machine learning. Doctors can monitor students' emotional well-being through a dashboard that highlights students showing signs of distress.

## Features

### Student Interface
- Secure login.
- Journal entry submission with automatic emotion classification.
- Personal emotion history viewing.

### Doctor Interface
- Secure login.
- Dashboard displaying students' emotional well-being.
- Alerts for students showing signs of distress.
- Access to students' journal entries.

## Technologies Used
- **Backend:** FastAPI
- **Frontend:** Streamlit
- **Machine Learning:** Hugging Face Transformers
- **Database:** SQLite
- **Containerization:** Docker
- **CI/CD:** GitHub Actions
- **Deployment:** Azure App Service, Azure Container Registry

## Prerequisites
- Docker installed on your local machine.
- Azure Account (for deployment).
- GitHub Account with access to the repository.

## Installation and Setup

### 1. Clone the Repository

git clone https://github.com/Nguinabe3/emotionapp.git
cd emotionapp
### 2. Build and Run the Docker Container
The application uses a Dockerfile that sets up both the FastAPI backend and Streamlit frontend in a single container.
### Application Files
- **main.py:** FastAPI backend
- **app.py:** Streamlit frontend

### Startup Command
- Starts Streamlit and then FastAPI within the same container.

### 3. Build and Run
docker build -t emotion-journal-app .
docker run -p 8000:8000 -p 8501:8501 emotion-journal-app
- Access the frontend at [http://localhost:8501](http://localhost:8501)
- Access the backend API at [http://localhost:8000](http://localhost:8000)

## Usage

### Access the Application
Open your web browser and navigate to [http://localhost:8501](http://localhost:8501).

### Default Users

#### Students
- **Username:** Najlaa, **Password:** password1
- **Username:** Mohamed, **Password:** password1

#### Doctors
- **Username:** Pedro, **Password:** password2
- **Username:** Kilian, **Password:** password2

## Continuous Integration and Deployment (CI/CD)
The project uses GitHub Actions for automated building and deployment to Azure.

- Docker Images are built and pushed to Azure Container Registry (ACR).
- Azure Web App runs the application using the Docker images.

## Deployment to Azure

### Prerequisites
- Azure CLI installed and logged in.
- Azure Subscription with necessary permissions.
## Deployment Steps

### 1. Create Azure Resources

az group create --name emotion-journal-rg --location eastus
az acr create --resource-group emotion-journal-rg --name emotionjournalacr --sku Basic
az appservice plan create --name emotion-journal-plan --resource-group emotion-journal-rg --is-linux --sku B1
az webapp create --resource-group emotion-journal-rg --plan emotion-journal-plan --name emotion-journal-app --multicontainer-config-type compose --multicontainer-config-file docker-compose.yml
### 2. Push Docker Image to ACR
Build and push the Docker image to your Azure Container Registry.


# Log in to ACR
az acr login --name emotionjournalacr

# Tag and push the image
docker tag emotion-journal-app emotionjournalacr.azurecr.io/emotion-journal-app:latest
docker push emotionjournalacr.azurecr.io/emotion-journal-app:latest

### 3. Configure Azure Web App
- Set up the web app to pull images from ACR.
- Assign the `AcrPull` role to the web app's managed identity.

## Project Structure

```bash
emotion-journal-app/
├── app.py                # Streamlit frontend
├── main.py               # FastAPI backend
├── requirements.txt      # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose configuration
└── README.md             # Project documentation


```
## License
This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for more details.
