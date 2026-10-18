let locationWatcher = null;


// ------------------------------------
// START LOCATION TRACKING
// ------------------------------------

function startLocationTracking() {

    const status =
        document.getElementById("location-status");

    if (!navigator.geolocation) {

        if (status) {

            status.innerText =
                "GPS is not supported by this browser.";

        }

        return;
    }


    if (status) {

        status.innerText =
            "📍 Starting GPS tracking...";

    }


    locationWatcher =
        navigator.geolocation.watchPosition(

            sendLocation,

            locationError,

            {
                enableHighAccuracy: true,
                maximumAge: 5000,
                timeout: 10000
            }

        );

}


// ------------------------------------
// SEND LOCATION TO FLASK
// ------------------------------------

function sendLocation(position) {

    const latitude =
        position.coords.latitude;

    const longitude =
        position.coords.longitude;


    const status =
        document.getElementById("location-status");


    const coordinates =
        document.getElementById("location-details");


    if (status) {

        status.innerText =
            "✓ Location tracking active.";

    }


    if (coordinates) {

        coordinates.innerHTML =

            "<strong>Latitude:</strong> " +
            latitude +

            "<br>" +

            "<strong>Longitude:</strong> " +
            longitude;

    }


    fetch("/driver/update-location", {

        method: "POST",

        headers: {
            "Content-Type": "application/json"
        },

        body: JSON.stringify({

            latitude: latitude,

            longitude: longitude

        })

    })

    .then(response => {

        if (!response.ok) {

            throw new Error(
                "Location update failed"
            );

        }

        return response.json();

    })

    .then(data => {

        console.log(
            "Location updated:",
            data
        );

    })

    .catch(error => {

        console.error(
            "Location error:",
            error
        );

        if (status) {

            status.innerText =
                "GPS obtained, but server update failed.";

        }

    });

}


// ------------------------------------
// LOCATION ERROR
// ------------------------------------

function locationError(error) {

    const status =
        document.getElementById("location-status");


    let message =
        "Unable to access GPS location.";


    if (error.code === 1) {

        message =
            "Location permission was denied.";

    }

    else if (error.code === 2) {

        message =
            "Location information is unavailable.";

    }

    else if (error.code === 3) {

        message =
            "Location request timed out.";

    }


    if (status) {

        status.innerText =
            "❌ " + message;

    }

    console.error(
        "GPS Error:",
        error
    );

}


// ------------------------------------
// STOP LOCATION TRACKING
// ------------------------------------

function stopLocationTracking() {

    if (locationWatcher !== null) {

        navigator.geolocation.clearWatch(
            locationWatcher
        );

        locationWatcher = null;

    }


    const status =
        document.getElementById("location-status");


    if (status) {

        status.innerText =
            "Location tracking stopped.";

    }

}


// ------------------------------------
// AUTOMATICALLY START
// ------------------------------------

// Start only if the current page
// contains the location status element.

if (
    document.getElementById("location-status")
) {

    startLocationTracking();

}