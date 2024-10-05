import subprocess
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json

app = FastAPI()

# Automatically install Mosquitto when the app starts
@app.on_event("startup")
async def install_mosquitto():
    try:
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "mosquitto", "mosquitto-clients"], check=True)
        print("Mosquitto installed successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Error during Mosquitto installation: {str(e)}")

# Endpoint to configure Mosquitto settings
class MosquittoConfig(BaseModel):
    listener_port: int
    allow_anonymous: bool

@app.post("/configure-mosquitto/")
async def configure_mosquitto(config: MosquittoConfig):
    try:
        mosquitto_conf = f"""
        listener {config.listener_port}
        allow_anonymous {str(config.allow_anonymous).lower()}
        password_file /etc/mosquitto/passwords.txt
        """
        with open("/etc/mosquitto/mosquitto.conf", "w") as file:
            file.write(mosquitto_conf)

        subprocess.run(["systemctl", "restart", "mosquitto"], check=True)
        return {"message": "Mosquitto configured successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Endpoint to add a new MQTT user
class AddUserRequest(BaseModel):
    username: str
    password: str

@app.post("/add-mqtt-user/")
async def add_mqtt_user(request: AddUserRequest):
    try:
        subprocess.run(["mosquitto_passwd", "-b", "/etc/mosquitto/passwords.txt", request.username, request.password], check=True)
        return {"message": f"User {request.username} added successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Endpoint to delete an MQTT user
@app.delete("/delete-mqtt-user/{username}")
async def delete_mqtt_user(username: str):
    try:
        subprocess.run(["mosquitto_passwd", "-D", "/etc/mosquitto/passwords.txt", username], check=True)
        return {"message": f"User {username} deleted successfully"}
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

# Endpoint to publish a message to a topic
class PublishRequest(BaseModel):
    topic: str
    message: str
    username: str
    password: str

@app.post("/publish/")
async def publish_message(request: PublishRequest):
    try:
        # Connect to Mosquitto and publish a message
        client = mqtt.Client()
        client.username_pw_set(request.username, request.password)
        client.connect("localhost", 1883)
        client.publish(request.topic, request.message)
        client.disconnect()
        return {"message": f"Message published to {request.topic}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error publishing message: {str(e)}")

# Endpoint to subscribe to a topic
@app.post("/subscribe/")
async def subscribe_to_topic(topic: str):
    try:
        client = mqtt.Client()

        def on_message(client, userdata, message):
            print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

        client.on_message = on_message
        client.connect("localhost", 1883)
        client.subscribe(topic)
        client.loop_start()  # Start the loop to receive messages
        return {"message": f"Subscribed to {topic}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error subscribing to topic: {str(e)}")
