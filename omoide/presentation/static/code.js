function goSearch() {
    // escape special symbols in query and relocate
    let element = document.getElementById("query_element")

    if (!element)
        return

    let searchParams = new URLSearchParams(window.location.search)
    searchParams.set('q', element.value)
    window.location.href = "/search?" + searchParams.toString();
}


async function loadMoreItems(endpoint, container) {
    // make request for new items if we scrolled low enough
    let scrollY = window.scrollY;
    let innerHeight = window.innerHeight;
    let offsetHeight = document.body.offsetHeight;

    if (scrollY + innerHeight > offsetHeight - 100) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Accept': 'application/json'
                }
            });
            const items = await response.json()
            renderMoreItems(container, items)
        } catch (err) {
            throw err
        }
    }
}

function renderMoreItems(container, items) {
    // actually insert new items into response
    for (const item of items) {
        let envelope = document.createElement('div')
        envelope.classList.add("envelope")

        if (item["is_collection"]) {
            envelope.classList.add("env-collection")
        }

        let link = document.createElement('a')
        link.href = item['href']

        if (item.name) {
            let name = document.createElement('p')
            name.innerText = item.name
            link.appendChild(name)
        }

        let img = document.createElement('img')
        img.src = item["thumbnail"]
        link.appendChild(img)

        envelope.appendChild(link)
        container.appendChild(envelope);
    }
}
