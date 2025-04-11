// ==UserScript==
// @name         degen Filter (Hotkey + Auto)
// @namespace    http://tampermonkey.net/
// @version      1.1
// @author       anonymous-machine
// @include      http://boards.4chan.org/*
// @include      https://boards.4chan.org/*
// @include      http://sys.4chan.org/*
// @include      https://sys.4chan.org/*
// @include      http://www.4chan.org/*
// @include      https://www.4chan.org/*
// @include      http://boards.4channel.org/*
// @include      https://boards.4channel.org/*
// @include      http://sys.4channel.org/*
// @include      https://sys.4channel.org/*
// @include      http://www.4channel.org/*
// @include      https://www.4channel.org/*
// @include      http://i.4cdn.org/*
// @include      https://i.4cdn.org/*
// @include      http://is.4chan.org/*
// @include      https://is.4chan.org/*
// @include      http://is2.4chan.org/*
// @include      https://is2.4chan.org/*
// @include      http://is.4channel.org/*
// @include      https://is.4channel.org/*
// @include      http://is2.4channel.org/*
// @include      https://is2.4channel.org/*
// @grant        none
// ==/UserScript==

(function () {
    'use strict';

    const listPass = ["anime pornography", "art"];
    const listFail = ["shit", "scat pornography"];
    const apiEndpoint = "https://127.0.0.1:19081/analyze";

async function checkImage(img) {
    let imageUrl = img.src;

    // If inside a <a class="fileThumb">, use its href (full-size image)
    const parent = img.closest('a.fileThumb');
    if (parent && parent.href) {
        imageUrl = parent.href;
    }

    if (!imageUrl) return;

    const body = {
        image_url: imageUrl,
        listPass: listPass,
        listFail: listFail
    };

    try {
        const response = await fetch(apiEndpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(body)
        });

        const result = await response.json();

        if (result.result === "fail") {
            img.remove();
            console.log(`🛑 Removed image: ${imageUrl}`);
        } else {
            console.log(`✅ Image passed: ${imageUrl}`);
        }

    } catch (error) {
        console.error("Error checking image:", error);
    }
}

    function processImages() {
        const images = document.querySelectorAll('img');

        images.forEach(img => {
            if (!img.dataset.checked) {
                img.dataset.checked = "true";
                //img.dataset.checked = "false";
                checkImage(img);
            }
        });
    }

    // Trigger every 60 seconds
    //setInterval(() => {
        //console.log("Running automatic image check...");
        //processImages();
    //}, 60000);

    // Trigger on hotkey (Ctrl/Cmd + Shift + I)
    /* window.addEventListener('keydown', (e) => {
        const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
        if (
            (isMac && e.metaKey && e.shiftKey && e.key === 'I') ||
            (!isMac && e.ctrlKey && e.shiftKey && e.key === 'I')
        ) {
            e.preventDefault();
            console.log("Manual hotkey image check triggered.");
            processImages();
        }
    });
    */

    //clickable floating button
    function addFloatingButton() {
        const button = document.createElement("button");
        button.textContent = "Check Images";
        button.style.position = "fixed";
        button.style.bottom = "20px";
        button.style.right = "20px";
        button.style.zIndex = "9999";
        button.style.padding = "10px 15px";
        button.style.backgroundColor = "#007bff";
        button.style.color = "white";
        button.style.border = "none";
        button.style.borderRadius = "5px";
        button.style.cursor = "pointer";
        button.style.boxShadow = "0 2px 5px rgba(0,0,0,0.3)";
        button.style.fontSize = "14px";

        button.addEventListener("click", () => {
            console.log("Button-triggered image check.");
            processImages();
        });

        document.body.appendChild(button);
    }

    // On page load, run initial check and add button
    window.addEventListener('load', () => {
        console.log("Initial check on load.");
        processImages();
        addFloatingButton();
    });

})();

