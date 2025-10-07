
      const $doctor = document.getElementById("doctorFilter");
      const $service = document.getElementById("serviceFilter");

      container.querySelectorAll("[data-room-name]").forEach((el) => {
        el.addEventListener("mouseenter", async () => {
          lastRoomEl = el;
          lastRoom =
            el.dataset.roomName || el.getAttribute("data-room-name") || "";
          const rect = el.getBoundingClientRect();

          if (!$doctor || !$doctor.value) {
            showTip("Выберите врача в фильтре ↑", rect);
            return;
          }

          let durMin = 30;
          try {
            const dicts = await loadDictsOnce?.();
            const sId = $service?.value || "";
            const svc = (dicts?.services || []).find(
              (x) => String(x.id) === String(sId)
            );
            durMin = svc?.duration_min || 30;
          } catch {}

          const viewDate = window.calendar?.getDate
            ? window.calendar.getDate()
            : new Date();
          const day = fmtYMD(viewDate);
          const today = fmtYMD(new Date());
          const isToday = day === today;
          const nowHM = new Date().toTimeString().slice(0, 5); // "HH:MM"

          try {
            if (abortCtrl) abortCtrl.abort();
            abortCtrl = new AbortController();
            showTip("Загрузка свободных слотов…", rect);

            const r = await fetch(ROUTES.freeSlots, {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                doctor_id: $doctor.value,
                room_name: lastRoom,
                date: day,
                duration_min: durMin,
              }),
              signal: abortCtrl.signal,
            });
            const data = await r.json();

            const min = (
              window.calendar?.getOption?.("slotMinTime") || "09:00:00"
            ).slice(0, 5);
            const max = (
              window.calendar?.getOption?.("slotMaxTime") || "21:00:00"
            ).slice(0, 5);

            const slots = (data?.slots || [])
              .filter((t) => t >= min && t < max)
              .filter((t) => !isToday || t >= nowHM)
              .slice(0, 8);

            const title = `<div style="font-weight:600;margin-bottom:4px;">${lastRoom}</div>`;
            const body = slots.length
              ? `Свободно: <b>${slots.join("</b>, <b>")}</b>`
              : "Свободных слотов нет";
            const hint = `<div style="margin-top:8px;opacity:.7;font-size:12px;">Клик — откроет «${lastRoom} — сегодня»</div>`;
            showTip(`${title}<div>${body}</div>${hint}`, rect);
          } catch (e) {
            if (e.name !== "AbortError") showTip("Ошибка сети", rect);
          }
        });
        el.addEventListener("mouseleave", hideLater);
      });

      window.addEventListener("scroll", () => {
        if (tip.style.display === "block") tip.style.display = "none";
      });
      window.addEventListener("resize", () => {
        if (tip.style.display === "block") tip.style.display = "none";
      });
    })();

    /* === LIVE rooms bar: status + next slot === */
    (function initRoomsBarLive() {
      const bar = document.getElementById("roomsBar");
      if (!bar) return;

      function render(data) {
