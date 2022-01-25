function goSearch() {
    // escape special symbols in query and relocate
    let element = document.getElementById("query_element")

    if (!element)
        return

    let searchParams = new URLSearchParams(window.location.search)
    searchParams.set('q', element.value)
    window.location.href = "/search?" + searchParams.toString();
}
