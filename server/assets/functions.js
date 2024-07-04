;(() => {
  function downloadString(filename, mime_type, text) {
    const pom = document.createElement("a")
    pom.setAttribute(
      "href",
      `data:${mime_type};charset=utf-8,` + encodeURIComponent(text)
    )
    pom.setAttribute("download", filename)
    pom.click()
  }

  /**
   * @returns {Promise<File>}
   */
  function openFile() {
    const input = document.createElement("input")
    input.type = "file"
    const ret = new Promise((resolve, reject) => {
      input.onchange = (_) => {
        const files = input.files
        if (!files || files.length === 0) {
          reject("No file selected")
        }
        resolve(input.files[0])
      }
    })
    input.click()
    return ret
  }

  function showMessage(message) {
    const box = document.createElement("div")
    box.classList.add("alert-box")
    box.innerHTML = message
    const close = () => document.body.removeChild(box)
    box.onclick = close
    setTimeout(close, 5000)
    document.body.appendChild(box)
  }

  window.dash_clientside ||= {}
  Object.assign(window.dash_clientside, {
    main: {
      exit_program: function (count) {
        console.log("Exiting program")
        if (count > 0) {
          if (confirm("确定要结束监控然后退出程序吗？")) {
            setTimeout(window.close, 200)
            return 1
          }
        }
        return 0
      },
      refresh_page: function (count) {
        if (count > 0) {
          location.reload()
        }
      },
      handle_save: function (text, filename) {
        if (text && filename) {
          downloadString(filename, "text/csv", text)
        }
      },
      /**
       * @param {number} n_clicks
       * @returns {Promise<string | null>}
       */
      handle_load: async function (n_clicks) {
        if (n_clicks <= 0) {
          return null
        }
        let file
        try {
          file = await openFile()
          const text = await file.text()
          return text
        } catch {
          return null
        }
      },
      show_message: function (message) {
        showMessage(message)
      },
    },
  })
})()
