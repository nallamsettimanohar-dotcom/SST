console.log("School Bus System loaded");


function startLocationTracking() {

    if (!navigator.geolocation) {

        alert("Geolocation is not supported by this browser.");

        return;
    }


    alert("Live location tracking started.");


    navigator.geolocation.watchPosition(

        function(position) {

            const latitude =
                position.coords.latitude;

            const longitude =
                position.coords.longitude;


            fetch("/api/location", {

                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    latitude: latitude,
                    longitude: longitude

                })

            })

            .then(response => response.json())

            .then(data => {

                console.log(
                    "Location updated:",
                    data
                );

            })

            .catch(error => {

                console.error(
                    "Location update error:",
                    error
                );

            });

        },


        function(error) {

            console.error(
                "GPS Error:",
                error
            );

            alert(
                "Unable to get location. Please allow location permission."
            );

        },


        {
            enableHighAccuracy: true,
            maximumAge: 5000,
            timeout: 10000
        }

    );

}