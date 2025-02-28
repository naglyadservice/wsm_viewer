# WSM Viewer

WSM Viewer - a web interface for monitoring and controlling water vending machines (vodomats) using the MQTT protocol.

## Description

The "WSM Viewer" project is designed for remote management of water vending machines in the "Vodomat" project. The system allows:

- Monitoring device status in real-time
- Managing vending machine settings and configuration
- Controlling water dispensing (two types)
- Processing various payment types (QR code, free crediting)
- Getting information from the device display
- Blocking/unblocking devices

## Technologies

- **Backend**: Python, Flask, Paho MQTT
- **Frontend**: JavaScript, Bootstrap 4
- **Authentication**: Flask-Login
- **Communication Protocol**: MQTT

## Installation

1. Clone the repository:
```bash
git clone https://github.com/ixcue/wsm_viewer.git
cd wsm_viewer
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # For Linux/Mac
# or
venv\Scripts\activate  # For Windows
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure environment variables:
```bash
cp .env.example .env
# Edit the .env file, specifying MQTT broker connection parameters
```

5. Run the application:
```bash
python app.py
```

## Usage

1. Open a web browser and go to: `http://localhost:5000`
2. Log in with the default credentials:
   - Login: `admin`
   - Password: `admin`
3. After logging in, you will see a list of discovered devices
4. Click on a device to access its management interface

## Project Structure

- `app.py` - main application file
- `config.py` - configuration settings
- `auth.py` - authorization functions
- `mqtt/client.py` - MQTT client for device communication
- `api/routes.py` - API routes for device interaction
- `templates/` - HTML templates
- `static/` - static files (JavaScript, CSS)

## MQTT Protocol

The project implements the "Vodomat" exchange protocol via MQTT. Main topics:

- `wsm/{device_id}/server/begin` - device startup information
- `wsm/{device_id}/server/state/info` - periodic status information
- `wsm/{device_id}/client/config/set` - configuration sending
- `wsm/{device_id}/client/setting/set` - project settings sending
- `wsm/{device_id}/client/action/set` - control commands sending
- `wsm/{device_id}/client/payment/set` - payment management

Full protocol documentation is available in the file `Protocol Exchange Description.docx`.

## License

All rights reserved. This code may not be used, copied, modified, or distributed without the explicit written permission of the author.

## Contact

If you have questions or wish to request permission to use this code, please create an Issue or contact us by email.
