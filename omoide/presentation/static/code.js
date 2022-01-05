function goSearch(form) {
    // escape special symbols in query and update parameters
    let element = document.getElementById("query_element");
    element.value = element.value.replaceAll("\,", "%2C")
    element.value = element.value.replaceAll("\+", "%2B")
    element.value = element.value.replaceAll(/\s+/g, "%20")

    let searchParams = new URLSearchParams(window.location.search);
    form.action = "/search?" + searchParams.toString();
}
