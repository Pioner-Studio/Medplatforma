        </button>
      </div>
      <small
        id="qm_warn"
        style="grid-column: 1/-1; color: #b45309; display: none"
        >Предупреждение</small
      >

      <div
        style="
          grid-column: 1/-1;
          display: flex;
          justify-content: flex-end;
          gap: 8px;
        "
      >
        <button
          type="button"
          id="qmDelete"
          class="btn"
          style="background: #fee2e2; border: 1px solid #fecaca"
        >
          Удалить
        </button>
        <button type="submit" class="btn btn-primary">Сохранить</button>
      </div>
    </form>
  </div>
</div>

<!-- Toasts -->
<div
  id="toastStack"
  style="
    position: fixed;
    right: 16px;
    top: 16px;
    z-index: 10000;
    display: flex;
    flex-direction: column;
    gap: 8px;
  "
></div>

{% endblock %} {% block scripts %}
<link
  rel="stylesheet"
  href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css"
/>
<link
  href="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.css"
  rel="stylesheet"
/>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/index.global.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/fullcalendar@6.1.11/locales-all.global.min.js"></script>

<script>
  // Точки API для тултипа «свободные слоты» и попапа «... — сегодня»
  const ROUTES = {
    freeSlots: "/api/free_slots",
    todayDetailsApi: "/api/rooms/today_details",
  };
</script>

<style>
  /* форма нового пациента — стабильно, без «вылазов» */
  #quickModal .qm-patient-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 8px;
    align-items: center;
  }
  #quickModal .qm-patient-grid input {
    width: 100%;
    height: 36px;
    padding: 8px 10px;
    border: 1px solid #dbeafd;
    border-radius: 8px;
    box-sizing: border-box;
  }
  #quickModal .qm-patient-grid input:focus {
    outline: none;
    border-color: #a5c5ff;
    box-shadow: 0 0 0 3px rgba(73, 133, 255, 0.12);
  }
  #quickModal .qm-patient-actions {
    display: flex;
    gap: 8px;
    justify-content: flex-start;
  }
  @media (min-width: 740px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 1fr;
    }
    #quickModal .qm-patient-grid > :first-child {
      grid-column: 1 / -1;
    } /* ФИО */
    #quickModal .qm-patient-actions {
      grid-column: 1 / -1;
    }
  }
  @media (min-width: 900px) {
    #quickModal .qm-patient-grid {
      grid-template-columns: 1fr 180px;
    }
  }

  /* PATCH: кликабельность и поведение подсказок */
  .ps-room-clickable {
    cursor: pointer;
  }
  .ps-free-hint,
  [data-free-hint] {
    pointer-events: auto;
  }
  [data-room],
  .ps-room,
  .room,
  .ps-rooms-item,
  [data-open-room] {
    cursor: pointer;
  }
</style>

<script>
  // --- простой toast ---
  function showToast(msg, type = "info", ms = 2200) {
    const stack = document.getElementById("toastStack");
    if (!stack) {
      alert(msg);
      return;
    }
    const el = document.createElement("div");
    el.textContent = msg;
    el.style.cssText = `
      background:${
        type === "error" ? "#fee2e2" : type === "ok" ? "#e6ffed" : "#eef2ff"
      };
      color:${
        type === "error" ? "#991b1b" : type === "ok" ? "#065f46" : "#1e40af"
