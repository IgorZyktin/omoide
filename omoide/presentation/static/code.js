const UUID_PREFIX_LENGTH = 2
const UUID_REGEXP = /[0-9A-F]{8}-[0-9A-F]{4}-[04][0-9A-F]{3}-[089AB][0-9A-F]{3}-[0-9A-F]{12}/ig

const EMPTY_FILE = '/static/empty.png'

const EXIF_ENDPOINT = '/api-new/v1/exif'
const METAINFO_ENDPOINT = '/api-new/v1/metainfo'
const MEDIA_ENDPOINT = '/api-new/v1/media'
const ITEMS_ENDPOINT = '/api-new/v1/items'
const ACTIONS_ENDPOINT = '/api-new/v1/actions'


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
    let target = document.getElementById(alertsElementId || 'alerts')
    let alert = document.createElement('div')

    alert.innerHTML = `
        <div class="notification ${css_class}">
            <span class="closebtn"
                  onclick="this.parentElement.style.display='none';">&times;</span>
            ${text}
        </div>`

    target.appendChild(alert)
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
    let alert = document.createElement('div')

    alert.innerHTML = `
        <div class="small-notification ${css_class}">
            <span class="closebtn"
                  onclick="$(this.parentElement).remove()">&times;</span>
            ${text}
        </div>`

    setInterval(() => {
        $(alert).remove()
    }, 4000)

    element.appendChild(alert)
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

function toggleConnected() {
    // toggle `connected/associated` search mode
    let searchParams = new URLSearchParams(window.location.search)

    if (searchParams.get('connected') === 'on')
        searchParams.set('connected', 'off')
    else
        searchParams.set('connected', 'on')

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

function renderThumbnailStatic(container, path) {
    // render single thumbnail during page edit (collection or singular)
    let envelope = $('<div>', {class: 'envelope'})
    envelope.appendTo(container)

    $('<img>', {
        src: path,
        alt: 'Thumbnail'
    }).css('maxWidth', '384px').appendTo(envelope)
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
    return text.replace(/\r\n/, '\n').split('\n').filter(n => n)
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
    // scroll to the bottom
    const scrollingElement = (document.scrollingElement || document.body);
    scrollingElement.scrollTop = scrollingElement.scrollHeight;
}

function jumpToTop(targetId) {
    // scroll to the top
    const scrollingElement = (document.scrollingElement || document.body);
    if (!targetId) {
        scrollingElement.scrollTop = 0;
    } else {
        document.getElementById(targetId).scrollIntoView()
    }
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

function addActiveGuess(items, currentFocus) {
    // Mark guess item as active
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
    return new Promise((resolve, reject) => {
        $.ajax({
            url: `${endpoint}?tag=${tag.trim()}`,
            type: 'GET',
            timeout: 10000,
            success: (response) => {
                resolve(response['variants']);
            },
            error: (response) => {
                reject(response);
            }
        })
    })
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
        item.innerHTML = body + separator
        item.innerHTML += '<strong>' + variant.substring(0, tag.length) + '</strong>';
        item.innerHTML += variant.substring(tag.length);
        item.innerHTML += "<input type='hidden' value='" + variant + "'>";
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
        $(header).addClass('header-floating').removeClass('header-static');
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
    if (!item.thumbnail_ext)
        return EMPTY_FILE

    let prefix = item.uuid.slice(0, UUID_PREFIX_LENGTH)
    return `/content/thumbnail/${item.owner_uuid}/${prefix}/${item.uuid}.${item.thumbnail_ext}`
}

function getPreviewContentUrl(item) {
    // generate preview content url for the item
    if (!item.preview_ext)
        return EMPTY_FILE

    let prefix = item.uuid.slice(0, UUID_PREFIX_LENGTH)
    return `/content/preview/${item.owner_uuid}/${prefix}/${item.uuid}.${item.preview_ext}`
}

function getContentUrl(item) {
    // generate preview content url for the item
    if (!item.content_ext)
        return EMPTY_FILE

    let prefix = item.uuid.slice(0, UUID_PREFIX_LENGTH)
    return `/content/content/${item.owner_uuid}/${prefix}/${item.uuid}.${item.content_ext}`
}

function getPreviewUrl(item) {
    // generate preview url for the item
    let searchParams = new URLSearchParams(window.location.search)
    if (item.is_collection) {
        return `/browse/${item.uuid}` + '?' + searchParams.toString()
    }
    return `/preview/${item.uuid}` + '?' + searchParams.toString()
}
