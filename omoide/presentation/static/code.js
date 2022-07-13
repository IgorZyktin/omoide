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
        envelope.classList.add('envelope')

        if (item.is_collection) {
            envelope.classList.add('env-collection')
        }

        let link = document.createElement('a')
        link.href = item['href']

        if (item.is_collection && item.name) {
            let name = document.createElement('p')
            name.innerText = item.name
            link.appendChild(name)
        }

        let img = document.createElement('img')
        img.src = item.thumbnail
        link.appendChild(img)

        envelope.appendChild(link)
        container.appendChild(envelope);
    }
}

function atTheBottom() {
    // return true if user scrolled at the end of the page
    let scrollY = window.scrollY
    let innerHeight = window.innerHeight
    let offsetHeight = document.body.offsetHeight
    return scrollY + innerHeight > offsetHeight - 100
}

async function dynamicallyLoadMoreItems(endpoint, container,
                                        callback, stopCallback) {
    // make request for new items if we scrolled low enough
    let scrollY = window.scrollY;
    let innerHeight = window.innerHeight;
    let offsetHeight = document.body.offsetHeight;

    if (scrollY + innerHeight > offsetHeight - 100) {
        await fetch(endpoint, {
            headers: {
                'Accept': 'application/json'
            }
        })
            .then(response => response.json())
            .then(function (response) {
                dynamicallyRenderMoreItems(container, response,
                    callback, stopCallback)
            }).catch(function (error) {
                console.log(error);
                stopCallback()
            });
    }
}

function dynamicallyRenderMoreItems(container, items,
                                    callback, stopCallback) {
    // actually insert new items into response
    let searchParams = new URLSearchParams(window.location.search)

    for (const item of items) {
        let ignore = callback(item);

        if (ignore)
            continue

        let envelope = document.createElement('div')
        envelope.classList.add('envelope')

        if (item.is_collection) {
            envelope.classList.add('env-collection')
        }

        let link = document.createElement('a')
        searchParams.set('page', '1')
        link.href = item['href'] + '?' + searchParams.toString()

        if (item.is_collection && item.name) {
            let name = document.createElement('p')
            name.innerText = item.name
            link.appendChild(name)
        }

        let img = document.createElement('img')
        img.src = item.thumbnail
        link.appendChild(img)

        envelope.appendChild(link)
        container.appendChild(envelope);

    }

    if (items.length < searchParams.get('items_per_page'))
        stopCallback()
}

function reloadSearchParams(newSearchParams) {
    // redirect using new search params
    window.location.href = window.location.origin
        + window.location.pathname + '?' + newSearchParams.toString();
}

function toggleOrdered() {
    // toggle random/ordered search mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('ordered') === 'on') {
        searchParams.set('ordered', 'off')
        searchParams.set('paged', 'off')
    } else
        searchParams.set('ordered', 'on')

    reloadSearchParams(searchParams)
}

function toggleNested() {
    // toggle nested/flat search mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('nested') === 'on')
        searchParams.set('nested', 'off')
    else
        searchParams.set('nested', 'on')

    reloadSearchParams(searchParams)
}

function togglePaged() {
    // toggle paged/dynamic load mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('paged') === 'on')
        searchParams.set('paged', 'off')
    else
        searchParams.set('paged', 'on')

    reloadSearchParams(searchParams)
}

function relocateWithAim(url, parameters) {
    // change current url with consideration of query parameters
    let searchParams = new URLSearchParams(window.location.search)
    for (const [key, value] of Object.entries(parameters || {})) {
        searchParams.set(key, value)
    }
    window.location.href = url + '?' + searchParams.toString();
}

function renderThumbnailDynamic(container, item) {
    // render single thumbnail during page edit (collection or singular)
    let envelope = $('<div>', {class: 'envelope'})
    if (item.is_collection) {
        envelope.addClass('env-collection')
    }
    envelope.appendTo(container)

    let link = $('<a>', {href: getPreviewUrl(item)})
    link.appendTo(envelope)

    if (item.is_collection && item.name) {
        $('<p>', {text: item.name}).appendTo(link)
    }

    $('<img>', {
        src: getThumbnailContentUrl(item),
        alt: 'Thumbnail for ' + (item.name ? item.name : item.uuid)
    }).appendTo(link)
}

function convertDatetimeToIsoString(datetime) {
  let tzo = -datetime.getTimezoneOffset(),
      dif = tzo >= 0 ? '+' : '-',
      pad = function(num) {
          return (num < 10 ? '0' : '') + num;
      };

  return datetime.getFullYear() +
      '-' + pad(datetime.getMonth() + 1) +
      '-' + pad(datetime.getDate()) +
      ' ' + pad(datetime.getHours()) +
      ':' + pad(datetime.getMinutes()) +
      ':' + pad(datetime.getSeconds()) +
      dif + pad(Math.floor(Math.abs(tzo) / 60)) +
      ':' + pad(Math.abs(tzo) % 60);
}
