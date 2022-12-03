const UUID_PREFIX_LENGTH = 2
const UUID_REGEXP = /[0-9A-F]{8}-[0-9A-F]{4}-[04][0-9A-F]{3}-[089AB][0-9A-F]{3}-[0-9A-F]{12}/ig

function goSearch() {
    // escape special symbols in query and relocate
    let element = document.getElementById("query_element")

    if (!element)
        return

    let searchParams = new URLSearchParams(window.location.search)
    searchParams.set('q', element.value)
    searchParams.set('page', '1')
    window.location.href = "/search?" + searchParams.toString();
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

function splitLines(text) {
    // split string by line separators and return only non-empty
    return text.replace(/\r\n/, '\n').split('\n').filter(n => n)
}

function arraysAreIdentical(arr1, arr2){
    if (arr1.length !== arr2.length) return false;
    for (let i = 0, len = arr1.length; i < len; i++){
        if (arr1[i] !== arr2[i]){
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

function getNonEmptyValues(array){
    // Return array without empty values
    return array.filter(x => x)
}

function jumpToTop() {
    // scroll at the top
    document.body.scrollTop = document.documentElement.scrollTop = 0;
}
