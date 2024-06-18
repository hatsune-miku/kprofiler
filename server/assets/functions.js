(() => {
  window.dash_clientside ||= {};
  Object.assign(window.dash_clientside, {
    main: {
      exit_program: function (count) {
        console.log("Exiting program");
        if (count > 0) {
          if (confirm("确定要结束监控然后退出程序吗？")) {
            window.close();
            return 1;
          }
        }
        return 0;
      },
      refresh_page: function (count) {
        if (count > 0) {
          location.reload();
        }
      },
    },
  });
})();
