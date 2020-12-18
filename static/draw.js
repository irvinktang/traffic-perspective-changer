window.onload = () => {
    let Markers = new Array()
    let points = new Array()
    const canvas = document.getElementById('canvas')
    const ctx = canvas.getContext('2d')
    let scale

    const draw = function () {
        const frameData = $('#frame-data').data()
        let img = new Image()
        let width
        let height
        img.onload = function() {
            if (img.width > img.height) {
                scale = 1000/img.width 
                width = 1000
                height = img.height * scale
            } else {
                scale = 1000/img.height
                height = 1000
                width = img.width * scale 
            }
            ctx.drawImage(img, 0, 0, width, height)
        }
        img.src = `data:image/jpeg;base64,${frameData.frame.slice(2,-1)}`
    }

    const Marker = function () {
        this.Sprite = new Image();
        this.Sprite.src = "http://www.clker.com/cliparts/w/O/e/P/x/i/map-marker-hi.png"
        this.Width = 12;
        this.Height = 20;
        this.XPos = 0;
        this.YPos = 0;
    }

    const mouseClicked = function(mouse) {
        const rect = canvas.getBoundingClientRect()
        const mouseXPos = (mouse.x - rect.left)
        const mouseYPos = (mouse.y - rect.top)

        const marker = new Marker()
        marker.XPos = mouseXPos - (marker.Width / 2)
        marker.YPos = mouseYPos - marker.Height
        if (Markers.length < 4) {
            marker.Sprite.onload = function() {
                ctx.drawImage(marker.Sprite, marker.XPos, marker.YPos, marker.Width, marker.Height)
            }
            Markers.push(marker)
            console.log([marker.XPos*(1/scale), marker.YPos*(1/scale)])
            points.push([marker.XPos*(1/scale), marker.YPos*(1/scale)])
        }
    }

    const transformClicked = function() {
        if (Markers.length < 4) {
            const error = document.getElementById('transform-error')
            error.removeAttribute('hidden')
            return false
        } else {
            let spinner = document.getElementById('loading')
            spinner.removeAttribute('style')
            $('.content').hide()
            let pointForm = document.forms['send-points']
            pointForm.points.value = points
        }
    }

    const undoClicked = function () {
        Markers = []
        points = []
        draw()
    }

    document.getElementById('transform').addEventListener('click', transformClicked)
    document.getElementById('undo').addEventListener('click', undoClicked)
    canvas.addEventListener('mousedown', mouseClicked, false)


    draw()
    
}
