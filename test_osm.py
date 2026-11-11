
import requests
import csv

url = "https://overpass.private.coffee/api/interpreter"

query = """
[out:json][timeout:15];
node["emergency"="shelter"](11.85,75.35,11.91,75.42);
out;
"""

try:
    response = requests.get(
        url,
        params={"data": query},
        timeout=60
    )

    response.raise_for_status()
    data = response.json()

    shelters = []

    for element in data["elements"]:

        tags = element.get("tags", {})

        name = tags.get(
            "name",
            "Unnamed Emergency Shelter"
        )

        latitude = element["lat"]
        longitude = element["lon"]

        shelters.append([
            name,
            latitude,
            longitude
        ])

    with open("shelters.csv", "w", newline="") as file:

        writer = csv.writer(file)

        writer.writerow([
            "name",
            "latitude",
            "longitude"
        ])

        writer.writerows(shelters)

    print("Total shelters found:", len(shelters))
    print("Shelter data saved successfully!")

except requests.exceptions.RequestException as error:
    print("Unable to connect to OpenStreetMap.")
    print("Error:", error)

except Exception as error:
    print("An error occurred:", error)
