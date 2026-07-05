const UUID_PREFIX_LENGTH = 2
const UUID_REGEXP = /[0-9A-F]{8}-[0-9A-F]{4}-[04][0-9A-F]{3}-[089AB][0-9A-F]{3}-[0-9A-F]{12}/ig

const EMPTY_FILE = '/static/empty.png'
const CREATED_FILE = '/static/created.png'

const METAINFO_ENDPOINT = '/api/v1/metainfo'
const ITEMS_ENDPOINT = '/api/v1/items'
const ACTIONS_ENDPOINT = '/api/v1/actions'


function makeAlert(text, alertsElementId) {
    // create alert popup message
    makeNotification(text, alertsElementId, 'om-alert')
}

function makeAnnounce(text, alertsElementId) {
    // create announce popup message
    makeNotification(text, alertsElementId, 'om-announce')
}

function makeNotification(text, alertsElementId, css_class) {
    // create user defined notification
    const target = document.getElementById(alertsElementId || 'alerts')
    if (!target) {
        return
    }

    const wrapper = document.createElement('div')
    const notification = document.createElement('div')
    notification.className = 'notification ' + css_class

    const close = document.createElement('span')
    close.className = 'closebtn'
    close.textContent = '×'  // &times;
    close.addEventListener('click', () => {
        notification.style.display = 'none'
    })
    notification.appendChild(close)

    // `text` is user-controlled (API messages, filenames, tag strings).
    // Append as a text node so any HTML in it is rendered literally.
    notification.appendChild(document.createTextNode(text))

    wrapper.appendChild(notification)
    target.appendChild(wrapper)
}

function makeSmallAlert(text, element) {
    // Make smaller than normal alert
    makeSmallNotification(text, element, 'om-alert')
}

function makeSmallAnnounce(text, element) {
    // Make smaller than normal announce
    makeSmallNotification(text, element, 'om-announce')
}

function makeSmallNotification(text, element, css_class) {
    // create user defined notification
    const wrapper = document.createElement('div')
    const notification = document.createElement('div')
    notification.className = 'small-notification ' + css_class

    const close = document.createElement('span')
    close.className = 'closebtn'
    close.textContent = '×'  // &times;
    close.addEventListener('click', () => {
        notification.remove()
    })
    notification.appendChild(close)

    // `text` is user-controlled (filenames, tag strings, API error
    // messages). Append as a text node — any HTML in it is literal.
    notification.appendChild(document.createTextNode(text))

    wrapper.appendChild(notification)
    setTimeout(() => wrapper.remove(), 4000)

    element.appendChild(wrapper)
}

async function copyText(text, title, alertId) {
    // Copy given text and announce it
    if (alertId === undefined) {
        alertId = 'copy-alerts'
    }

    let element = document.getElementById(alertId)
    if (!element) {
        console.error('Nowhere to put copy alert!')
        return
    }

    if (!text) {
        makeSmallAnnounce(`Nothing to copy!`, element)
        return
    }

    try {
        await navigator.clipboard.writeText(text);
        makeSmallAnnounce(`Copied ${title}!`, element)
    } catch (err) {
        makeSmallAlert(`Failed to copy ${title}: ${err}`, element)
    }
}

function goSearch() {
    // escape special symbols in query and relocate
    let element = document.getElementById('query_element')

    if (!element)
        return

    let searchParams = new URLSearchParams(window.location.search)
    searchParams.set('q', element.value)
    searchParams.set('page', '1')
    window.location.href = '/search?' + searchParams.toString();
}

function reloadSearchParams(newSearchParams) {
    // redirect using new search params
    window.location.href = window.location.origin
        + window.location.pathname + '?' + newSearchParams.toString();
}

function toggleOrder() {
    // toggle `random/order` search mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('order') === 'asc') {
        searchParams.set('order', 'random')
        searchParams.set('page', '0')
    } else {
        searchParams.set('order', 'asc')
    }

    reloadSearchParams(searchParams)
}

function toggleDirect() {
    // toggle `direct/related` search mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('direct') === 'on')
        searchParams.set('direct', 'off')
    else
        searchParams.set('direct', 'on')

    reloadSearchParams(searchParams)
}

function toggleCollections() {
    // toggle `collections/all items` browse mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('collections') === 'on')
        searchParams.set('collections', 'off')
    else
        searchParams.set('collections', 'on')

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
    const envelope = document.createElement('div')
    envelope.classList.add('envelope')
    if (item.is_collection) {
        envelope.classList.add('env-collection')
    }
    container.append(envelope)

    const link = document.createElement('a')
    link.href = getPreviewUrl(item)
    envelope.append(link)

    if (item.is_collection && item.name) {
        const caption = document.createElement('p')
        caption.textContent = item.name
        link.append(caption)
    }

    const img = document.createElement('img')
    img.src = getThumbnailContentUrl(item)
    img.alt = 'Thumbnail for ' + (item.name ? item.name : item.uuid)
    img.width = item.extras.thumbnail_width
    img.height = item.extras.thumbnail_height
    link.append(img)
    img.addEventListener('load', updateImageSize);
}

function renderThumbnailStatic(container, path) {
    // render single thumbnail during page edit (collection or singular)
    const envelope = document.createElement('div')
    envelope.classList.add('envelope')
    container.append(envelope)

    const img = document.createElement('img')
    img.src = path
    img.alt = 'Thumbnail'
    img.style.maxWidth = '384px'
    envelope.append(img)
}

function updateImageSize() {
      // Read real dimensions and overwrite the placeholder properties
      this.width = this.naturalWidth;
      this.height = this.naturalHeight;
}

function convertDatetimeToIsoString(datetime) {
    let tzo = -datetime.getTimezoneOffset(),
        dif = tzo >= 0 ? '+' : '-',
        pad = function (num) {
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

function splitLines(text) {
    // split string by line separators and return only non-empty
    return text.replace(/\r\n/g, '\n').split('\n').filter(n => n)
}

function arraysAreIdentical(arr1, arr2) {
    if (arr1.length !== arr2.length) return false;
    for (let i = 0, len = arr1.length; i < len; i++) {
        if (arr1[i] !== arr2[i]) {
            return false;
        }
    }
    return true;
}

function extractUUIDs(text) {
    // extract all UUIDs from given text
    return [...text.matchAll(UUID_REGEXP)].flat()
}

function extractAllUUIDs(array) {
    // extract all UUIDs from given text
    let result = []
    for (const element of array) {
        let uuids = extractUUIDs(element) || []
        result = result.concat(uuids)
    }
    return getNonEmptyValues(result)
}

function getNonEmptyValues(array) {
    // Return array without empty values
    return array.filter(x => x)
}

function jumpToBottom() {
    // Scroll to the bottom of the page
    const maxScroll = document.body.scrollHeight - window.innerHeight;
    window.scrollTo({
        top: maxScroll,
        behavior: 'smooth'
    });
}

function jumpToTop() {
    // Scroll to the top of the page
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
}

function clearAutocompletion(element) {
    // Hide all autocomplete tags
    let items = document.getElementsByClassName('autocomplete-items')
    let inp = document.getElementById('query_element')

    for (let i = 0; i < items.length; i++) {
        if (element !== items[i] && element !== inp) {
            items[i].parentNode.removeChild(items[i]);
        }
    }
}

function highlightActiveVariant(items, currentFocus) {
    // Mark autocompletion variant item as active
    if (!items)
        return -1

    removeActive(items);

    if (currentFocus >= items.length) currentFocus = 0
    if (currentFocus < 0) currentFocus = (items.length - 1)
    items[currentFocus].classList.add('autocomplete-active')
    return currentFocus
}

function removeActive(element) {
    // Mark all guesses as inactive
    for (let i = 0; i < element.length; i++) {
        element[i].classList.remove('autocomplete-active');
    }
}

async function getAutocompletionVariants(tag, endpoint) {
    // Load possible autocompletion variants
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 10000)
    try {
        const response = await fetch(
            `${endpoint}?tag=${encodeURIComponent(tag.trim())}`,
            {method: 'GET', signal: controller.signal},
        )
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`)
        }
        const data = await response.json()
        return data['variants']
    } finally {
        clearTimeout(timeoutId)
    }
}

function escapeRegex(text) {
    // Escape characters that have special meaning in a regular expression.
    return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function appendWithHighlight(target, text, template) {
    // Append `text` to `target`, wrapping every case-insensitive
    // occurrence of `template` in a <strong> element. All inserted
    // strings go through textContent / data nodes, so neither `text`
    // nor `template` can carry HTML into the DOM.
    if (!template) {
        target.appendChild(document.createTextNode(text))
        return
    }
    const reg = new RegExp(escapeRegex(template), 'gi')
    let lastIndex = 0
    let match
    while ((match = reg.exec(text)) !== null) {
        if (match.index > lastIndex) {
            target.appendChild(
                document.createTextNode(text.slice(lastIndex, match.index)),
            )
        }
        const strong = document.createElement('strong')
        strong.textContent = match[0]
        target.appendChild(strong)
        lastIndex = match.index + match[0].length
        if (match[0].length === 0) {
            reg.lastIndex++  // guard against zero-length match infinite loop
        }
    }
    if (lastIndex < text.length) {
        target.appendChild(document.createTextNode(text.slice(lastIndex)))
    }
}

function splitLastTag(text) {
    // Extract last tag from user input
    let plusIndex = text.lastIndexOf(' + ')
    let minusIndex = text.lastIndexOf(' - ')

    let index = -1
    let separator = ''

    if (plusIndex > minusIndex) {
        separator = ' + '
        index = plusIndex
    } else if (minusIndex > -1) {
        separator = ' - '
        index = minusIndex
    }

    if (index === -1) {
        return ['', '', text]
    }

    let body = text.substring(0, index)
    let lastTag = text.substring(index + 3, text.length)

    return [body, separator, lastTag]
}

async function autocompleteTag(element, endpoint) {
    // Help user by guessing tag
    clearAutocompletion();

    let text = element.value

    if (!text) {
        return
    }

    const [body, separator, tag] = splitLastTag(text)

    if (tag.length <= 1) {
        clearAutocompletion();
        return
    }

    let dropdown = document.createElement('div');
    dropdown.setAttribute('id', element.id + 'autocomplete-list');
    dropdown.setAttribute('class', 'autocomplete-items');
    element.parentNode.appendChild(dropdown);

    let variants = await getAutocompletionVariants(tag, endpoint)

    for (const variant of variants) {
        let item = document.createElement('div');
        // `body + separator` is the user's own input minus the partial
        // last tag; render as a text node, never as HTML.
        item.appendChild(document.createTextNode(body + separator))
        // The variant comes from the server (a tag string originally
        // entered by some user). Highlight the matching prefix safely.
        appendWithHighlight(item, variant, tag)
        // Hidden input that the click handler reads to assemble the
        // final value. Setting .value attaches it as a DOM property,
        // not as an attribute-string, so quotes/HTML in `variant` are
        // stored verbatim and cannot break out.
        const hidden = document.createElement('input')
        hidden.type = 'hidden'
        hidden.value = variant
        item.appendChild(hidden)
        item.addEventListener('click', function (e) {
            let ending = this.getElementsByTagName('input')[0].value;
            element.value = body + separator + ending + ' '
            clearAutocompletion();
            setFocusAtTheEnd(element)
        });
        dropdown.appendChild(item);
    }
}

function setFocusAtTheEnd(input) {
    // Set cursor to the end of the input element
    let textLen = (input.value || '').length
    input.focus();
    input.setSelectionRange(textLen, textLen);
}

function activateFloatingHeader() {
    // Set header as active on specific pages
    let header = document.getElementById('header')

    if (header) {
        header.classList.add('header-floating')
        header.classList.remove('header-static')
    }
}

function updateHeaderPadding() {
    // Adjust header height so content will not be cropped
    let header = document.getElementById('header')
    let content = document.getElementById('content')

    if (header && content) {
        content.style.paddingTop = (header.clientHeight).toString() + 'px'
    }
}

function getThumbnailContentUrl(item) {
    // generate thumbnail content url for the item
    if (!item.thumbnail_ext) {
        if (item.status === 'created')
            return CREATED_FILE
        return EMPTY_FILE
    }

    let prefix = item.uuid.slice(0, UUID_PREFIX_LENGTH)
    return `/content/thumbnail/${item.owner_uuid}/${prefix}/${item.uuid}.${item.thumbnail_ext}`
}

function getPreviewUrl(item) {
    // generate preview url for the item
    let searchParams = new URLSearchParams(window.location.search)
    if (item.is_collection) {
        return `/browse/${item.uuid}` + '?' + searchParams.toString()
    }
    return `/preview/${item.uuid}` + '?' + searchParams.toString()
}


function itemIsVideo(item) {
    // Return true if item has video content
    return item.content_ext === 'mp4' || item.content_ext === 'webm'
}
