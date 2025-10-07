
<!-- GENERATED: 2025-09-08 16:08:04 -->

# calendar.html — patient search HTML

~~~html
/* NOT FOUND: patient search HTML */
~~~

---

# calendar.html — mini-search JS

~~~javascript
    // === MINI-SEARCH ПАЦИЕНТА: выбор элемента по pointerdown (фиксируем blur) ===
    (function initPatientMiniSearchSelection() {
      // Попробуем найти элементы по нескольким селекторам — под разные верстки
      const $input =
        document.getElementById("patientSearch") ||
        document.querySelector('[data-role="patient-search"]') ||
        document.querySelector('input[name="patient_search"]');
      const $menu =
        document.getElementById("patientSearchMenu") ||
        document.querySelector('[data-role="patient-search-menu"]') ||
        document.querySelector(
          "#patientSearch + .dropdown, #patientSearchMenu, .patient-mini-menu"
        );

      if (!$input || !$menu) return; // если нет — ничего не ломаем

      // Если пользователь снова печатает, сбрасываем выбранного пациента
      $input.addEventListener("input", () => {
        $input.dataset.patientId = "";
      });

      // Выбор пациента ДО того, как инпут потеряет фокус (главное — pointerdown + preventDefault)
      $menu.addEventListener(
        "pointerdown",
        (e) => {
          const item = e.target.closest("[data-patient-id]");
          if (!item) return;
          e.preventDefault(); // блокируем blur, чтобы меню не закрылось раньше времени

          const id = item.getAttribute("data-patient-id");
          const name =
            item.getAttribute("data-patient-name") || item.textContent.trim();

          // Проставляем выбранного пациента в инпут и в data-атрибут
          $input.value = name;
          $input.dataset.patientId = id;

          // Если у тебя есть скрытое поле для patient_id — тоже обновим (необязательно)
          const hidden =
            document.getElementById("patientId") ||
            document.querySelector('input[name="patient_id"]');
          if (hidden) hidden.value = id;

          // Закрыть меню (если есть класс/функция скрытия — дерни её; иначе просто спрячем)
          if ($menu.classList.contains("open")) $menu.classList.remove("open");
          $menu.style.display = "none";

          // Тригерим «выбор состоялся» и перезагружаем события
          $input.dispatchEvent(
            new CustomEvent("patient:selected", { detail: { id, name } })
          );
          try {
            calendar.refetchEvents();
          } catch (_) {}
        },
        { capture: true }
      );

      // По фокусу на инпуте снова показываем меню, если там что-то есть
      $input.addEventListener("focus", () => {
        if ($menu.children.length) {
          $menu.style.display = "block";
          $menu.classList.add("open");
        }
      });
    })();

    async function saveMoveOrResize(info) {
      const payload = {
        id: info.event.id,
        start: info.event.startStr,
        end: info.event.endStr || info.event.startStr,
      };
      try {
        const r = await fetch("/api/appointments/update_time", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        const data = await r.json();
        if (!data.ok) {
          alert(
            data.error === "room_conflict"
              ? "Конфликт: кабинет занят"
              : "Ошибка сохранения"
          );
          info.revert();
          return;
        }
        calendar.refetchEvents();
      } catch {
        alert("Сеть недоступна");
        info.revert();
      }
    }

    // открыть существующую
    async function openQuickModal(id) {
      try {
        const d = await loadDictsOnce();
        fillOptions(qm.doctor, d.doctors);
        fillOptions(qm.patient, d.patients);
        fillOptions(qm.service, d.services);
        fillOptions(qm.room, d.rooms);

        hideNewPatientRow(); // всегда скрываем «Новый пациент» в режиме редактирования

        const r = await fetch(`/api/appointments/${id}`);
        const data = await r.json();
        if (!data.ok) {
          showToast("Не удалось получить запись", "error");
          return;
        }
        const it = data.item;

        if (qm.id) qm.id.value = it.id || "";
        if (qm.doctor) qm.doctor.value = it.doctor_id || "";
        if (qm.patient) qm.patient.value = it.patient_id || "";
        await fillContactBar(qm.patient?.value || "");
        if (qm.service) qm.service.value = it.service_id || "";
        if (qm.room) qm.room.value = it.room_id || "";
~~~

---

# calendar.html — events fetch

~~~javascript
      events: (fetchInfo, success, failure) => {
        const params = new URLSearchParams({
          start: fetchInfo.startStr,
          end: fetchInfo.endStr,
        });
        const doctorSel = $("#doctorFilter"),
          serviceSel = $("#serviceFilter"),
          cabinetSel = $("#cabinetFilter");
        if (doctorSel?.value) params.set("doctor_id", doctorSel.value);
        if (serviceSel?.value) params.set("service_id", serviceSel.value);
        if (cabinetSel?.value) params.set("room_name", cabinetSel.value);

        // ✦ наш фильтр по пациенту
        if (window.psSelectedPatientId) {
          params.set("patient_id", window.psSelectedPatientId);
        }

        fetch("/api/events?" + params.toString())
          .then((r) => r.json())
          .then((data) => success(data))
          .catch((err) => {
            console.error("events load error", err);
            failure(err);
          });
      },

      eventDidMount(info) {
        const p = info.event.extendedProps || {};
        info.el.title = [p.service, p.patient, p.status]
          .filter(Boolean)
          .join(" • ");
      },

      eventDrop: saveMoveOrResize,
      eventResize: saveMoveOrResize,

      eventClick: async (info) => {
        setModalMode("edit");
        await openQuickModal(info.event.id);
      },

      dateClick: async (arg) => {
        try {
          const d = await loadDictsOnce();
          const doctorSel = document.getElementById("doctorFilter");
          fillOptions(qm.doctor, d.doctors, doctorSel?.value || "");
          fillOptions(qm.patient, d.patients);
          fillOptions(qm.service, d.services);
          fillOptions(qm.room, d.rooms);
          await fillContactBar(qm.patient?.value || "");

          hideNewPatientRow(); // по умолчанию скрыто; откроется только по кнопке «+ Новый»

          const roundTo = 15;
          const s = new Date(arg.date);
          s.setMinutes(Math.round(s.getMinutes() / roundTo) * roundTo, 0, 0);
          const e = addMin(s, 30);

          if (qm.id) qm.id.value = "";
          if (qm.start) qm.start.value = fmtISO(s);
          if (qm.end) qm.end.value = fmtISO(e);

          updateFirstFreeBtnState();
          await recalcEndByService().catch(() => {});
          await checkDoctorWorking().catch(() => {});

          setModalMode("create");
          openModal();
        } catch (e) {
          console.error(e);
          showToast("Не удалось открыть форму создания", "error");
        }
      },
    });

    calendar.render();
    window._calendar = calendar;
    window.calendar = calendar;

    // === HOVER ПО КАБИНЕТУ: показать ближайшие свободные слоты ===
    (function initRoomHoverFreeSlots() {
      const container = document.getElementById("roomsBar");
      if (!container) return;

      // минимальный tooltip без зависимостей
      const tip = document.createElement("div");
      tip.id = "roomTip";
      tip.style.cssText =
        "position:fixed;z-index:5000;display:none;background:#fff;border:1px solid #dbeafd;border-radius:10px;box-shadow:0 8px 24px rgba(0,0,0,.08);padding:10px 12px;font-size:.95rem;line-height:1.35;";
      document.body.appendChild(tip);

      let abortCtrl = null;
      const $doctor = document.getElementById("doctorFilter");
      const $service = document.getElementById("serviceFilter");

      function fmtYMD(d) {
        return `${d.getFullYear()}-${pad2(d.getMonth() + 1)}-${pad2(
          d.getDate()
        )}`;
      }
      function showTip(html, rect) {
        tip.innerHTML = html;
        tip.style.left = Math.round(rect.left) + "px";
        tip.style.top = Math.round(rect.bottom + 6 + window.scrollY) + "px";
        tip.style.display = "block";
      }
      function hideTip() {
        tip.style.display = "none";
        if (abortCtrl) abortCtrl.abort();
        abortCtrl = null;
      }

      container.querySelectorAll("[data-room-name]").forEach((el) => {
        el.addEventListener("mouseenter", async () => {
          const room =
            el.dataset.roomName || el.getAttribute("data-room-name") || "";
          const rect = el.getBoundingClientRect();

          if (!$doctor || !$doctor.value) {
            showTip("Выберите врача в фильтре ↑", rect);
            return;
          }

          showTip("Загрузка свободных слотов…", rect);

          // получаем длительность выбранной услуги из кеша словарей
          let durMin = 30;
          try {
            const dicts = await loadDictsOnce(); // уже есть в твоём файле
            const sId = $service?.value || "";
            const svc = (dicts.services || []).find(
              (x) => String(x.id) === String(sId)
            );
            durMin = svc?.duration_min || 30;
          } catch (e) {
            durMin = 30;
          }

          const day = fmtYMD(calendar.getDate()); // текущая дата в календаре

          try {
            abortCtrl = new AbortController();
            const r = await fetch("/api/free_slots", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                doctor_id: $doctor.value,
                room_name: room,
                date: day,
                duration_min: durMin,
              }),
~~~

---

# main.py — /api/events handler

~~~python
# NOT FOUND: @app.route('/api/events', methods=['GET']) block
~~~

---

