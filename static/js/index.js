let addIntervalButton = document.getElementById('addInterval');
let start = document.getElementById('inputStartTime');
let end = document.getElementById('inputEndTime');
let timeLine = document.getElementById('timeline');
let formIntervals = document.getElementById('intervalsInput');
let settingsBtn = document.getElementById('settingsBtn');
let sourceSelect = document.getElementById('sourceSelect');
let videoStream = document.getElementById('videoStream');
let baseUrl = 'http://127.0.0.1:8000/'

async function getSources () {
    let sources_url = new URL(`sources`, baseUrl)
    let sources_response = await fetch(sources_url);
    if (sources_response.ok) {
          let sources = await sources_response.json();
          for (let i = 0; i < sources.length; i++){
                var opt = document.createElement('option');
                opt.value = sources[i];
                opt.innerHTML = sources[i];
                if (i == 0) {
                   opt.selected = true
                }
                sourceSelect.appendChild(opt);
          }

    } else {
      alert("HTTP error: " + sources_response.status);
    }
}

async function postData(url = '', data = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(data)
    });
    return await response;
}

document.addEventListener("DOMContentLoaded", (event) => {
    getSources()
});



document.getElementById('playVideo').onclick = async function () {
    let settings_url = new URL(`play_video/${sourceSelect.value}`, baseUrl)
    let response = await fetch(settings_url);
    if (response.ok) {
        alert("Video started");
    }
}
document.getElementById('stopVideo').onclick = async function () {
    let settings_url = new URL(`stop_video/${sourceSelect.value}`, baseUrl)
    let response = await fetch(settings_url);
    if (response.ok) {
        alert("Video stopped");
    }
}

document.getElementById('saveSettingsBtn').onclick = function () {
    let settings_save_url = new URL(`video_settings/${sourceSelect.value}`, baseUrl)
    console.log(settings)
    postData(settings_save_url, settings)
}

let merged_intervals

let merged_time_intervals = ''

let settings

settingsBtn.onclick = async function () {
    let settings_url = new URL(`video_settings/${sourceSelect.value}`, baseUrl)
    let response = await fetch(settings_url);
    if (response.ok) {
      settings = await response.json();
      merged_intervals = settings.start.intervals
      document.getElementById('source_name').value = sourceSelect.value
      document.getElementById('video_source').value = settings.create.video_source
      document.getElementById('x0').value = settings.create.crop[2]
      document.getElementById('x1').value = settings.create.crop[3]
      document.getElementById('y0').value = settings.create.crop[0]
      document.getElementById('y1').value = settings.create.crop[1]
      document.getElementById('unknown_save_step').value = settings.start.unknown_save_step
      document.getElementById('width').value = settings.start.width
      document.getElementById('skipped_frames_coeff').value = settings.start.skipped_frames_coeff
      document.getElementById('faces_distance').value = settings.start.faces_distance
      document.getElementById('is_record').checked = settings.stream.is_record
      document.getElementById('is_recognized').checked = settings.stream.is_recognized
      intervalsToTimeLine(merged_intervals)
    } else {
      alert("HTTP error: " + response.status);
    }
}

sourceSelect.onchange = function () {
    let video_url = new URL(`video_stream/${sourceSelect.value}`, baseUrl)
    videoStream.src = video_url
}

addIntervalButton.onclick = function() {
   let interval = []
   interval.push(convertTimeToMinutes(start.value))
   interval.push(convertTimeToMinutes(end.value))
   merged_intervals.push(interval)
   merged_intervals = merge(merged_intervals)
   intervalsToTimeLine(merged_intervals)
};

document.addEventListener('click', handleClick)

function handleClick (event) {
    if (event.srcElement.id.includes('delbtn')) {
        let id = event.srcElement.id.split('-')
        delete_Interval(Number(id[1]))
        event.srcElement.offsetParent.remove()
    }
}

function delete_Interval(n) {
  console.log(n)
  merged_intervals.splice(n, 1)
  intervalsToTimeLine(merged_intervals)
}

function intervalsToTimeLine (merged_intervals) {
    const minutesInDay = 1440
    let lastPointEndMinute = 0
    timeLine.innerHTML = ''
    merged_time_intervals = ''
    for (let i = 0; i < merged_intervals.length; i++) {
        let startMinute = merged_intervals[i][0]
        let endMinute = merged_intervals[i][1]
        let emptyInterval = Math.round((startMinute - lastPointEndMinute) / 14.4)
        lastPointEndMinute = endMinute
        let fillInterval = Math.round((endMinute - startMinute) / 14.4)

        startTime = convertMinutesToTime(startMinute)
        endTime = convertMinutesToTime(endMinute)
        merged_time_intervals += startTime + '-' + endTime + ','

        let deleteButton = createElementFromHTML(`
            <div class="btn btn-danger btn-sm" id="delbtn-${i}">Delete</div>
        `)

        timeLine.innerHTML += `
            <span class="progress-bar" style="width: ${emptyInterval}%; background-color: #eaecf4"
                  aria-valuenow="${emptyInterval}" aria-valuemin="0" aria-valuemax="100"
            ></span>
            <span class="bg-success example-popover" style="width: ${fillInterval}%"
                  aria-valuenow="${fillInterval}" aria-valuemin="0" aria-valuemax="100"
                  data-container="body" data-toggle="popover" data-placement="top" data-html="true"
                  data-content='
                    <span class="mr-2">${startTime}-${endTime}</span>
                    ${deleteButton.outerHTML}
                  '
            ></span>
        `
    }
    $(function popoverUpdate () {
        $('[data-toggle="popover"]').popover()
   })
   formIntervals.value = merged_time_intervals
   console.log(formIntervals.value)
}


function createElementFromHTML(htmlString) {
  var div = document.createElement('div');
  div.innerHTML = htmlString.trim();

  return div.firstChild;
}

function convertTimeToMinutes (time) {
   let a = time.split(':');
   return (+a[0]) * 60 + (+a[1]);
}

function convertMinutesToTime (mins) {
    let hours = Math.trunc(mins/60);
    let minutes = mins % 60;
    if (minutes < 10) {
        minutes = '0' + minutes
    }
    return hours + ':' + minutes;
}

const merge = (intervals) => {
  if (intervals.length < 2) {
    return intervals
  }

  const sortedIntervals = intervals.sort((a, b) => a[0] - b[0])

  const result = [sortedIntervals[0]]

  for (let i = 0; i < sortedIntervals.length; i++) {
    let lastEnd = result[result.length - 1][1]

    let current = intervals[i]
    let currentStart = current[0]
    let currentEnd = current[1]

    if (currentStart <= lastEnd) {
      // пересекаются
      result[result.length - 1][1] = Math.max(lastEnd, currentEnd)
    } else {
      // не пересекаются
      result.push(current)
    }
  }
  return result
}

