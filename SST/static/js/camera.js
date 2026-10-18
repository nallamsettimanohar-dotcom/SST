let cameraStream = null;


// ------------------------------------
// START CAMERA
// ------------------------------------

async function startCamera() {

    const video =
        document.getElementById("camera-video");


    const status =
        document.getElementById("camera-status");


    const message =
        document.getElementById("camera-message");


    // Driver camera

    if (!video) {

        console.log(
            "Driver camera element not found."
        );

        return;

    }


    try {

        cameraStream =
            await navigator.mediaDevices.getUserMedia({

                video: true,

                audio: true

            });


        video.srcObject =
            cameraStream;


        if (status) {

            status.innerText =
                "🟢 Camera is active.";

        }


        if (message) {

            message.innerText =
                "Camera is currently streaming.";

        }


    }

    catch (error) {

        console.error(
            "Camera error:",
            error
        );


        if (status) {

            status.innerText =
                "🔴 Unable to access camera.";

        }


        if (message) {

            message.innerText =
                "Please allow camera and microphone permission.";

        }

    }

}


// ------------------------------------
// STOP CAMERA
// ------------------------------------

function stopCamera() {

    if (cameraStream) {

        const tracks =
            cameraStream.getTracks();


        tracks.forEach(
            track => track.stop()
        );


        cameraStream = null;

    }


    const video =
        document.getElementById("camera-video");


    const status =
        document.getElementById("camera-status");


    const message =
        document.getElementById("camera-message");


    if (video) {

        video.srcObject = null;

    }


    if (status) {

        status.innerText =
            "🔴 Camera is offline.";

    }


    if (message) {

        message.innerText =
            "Camera has been stopped.";

    }

}


// ------------------------------------
// PARENT CAMERA
// ------------------------------------

// The parent's page does not directly
// access the device camera.
//
// It will receive a stream from the
// bus camera through the server/WebRTC
// implementation that we add later.

function initializeParentCamera() {

    const status =
        document.getElementById(
            "parent-camera-status"
        );


    const message =
        document.getElementById(
            "parent-camera-message"
        );


    if (!status) {

        return;

    }


    status.innerText =
        "🟡 Waiting for bus camera stream.";


    if (message) {

        message.innerText =
            "Live stream will appear when the bus camera is connected.";

    }

}


// ------------------------------------
// PAGE DETECTION
// ------------------------------------

if (
    document.getElementById(
        "parent-camera-status"
    )
) {

    initializeParentCamera();

}