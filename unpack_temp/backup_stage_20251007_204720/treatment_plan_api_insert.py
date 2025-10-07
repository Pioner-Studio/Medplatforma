
# ============================================================================
# API: Treatment Plans (Планы лечения)
# ============================================================================

@app.route('/api/patients/<patient_id>/treatment-plans')
@login_required
def api_patient_treatment_plans(patient_id):
    """API для получения планов лечения пациента"""
    try:
        patient_oid = ObjectId(patient_id)
    except:
        return jsonify({"error": "Invalid patient ID"}), 400
    
    # Получаем все планы пациента, отсортированные по дате создания
    plans = list(db.treatment_plans.find({
        "patient_id": patient_oid
    }).sort("created_at", -1))
    
    result = []
    for plan in plans:
        # Получаем врача
        doctor = db.doctors.find_one({"_id": plan["doctor_id"]}) if plan.get("doctor_id") else None
        
        # Рассчитываем общую стоимость
        total_cost = sum(service.get("price", 0) for service in plan.get("services", []))
        
        # Считаем выполненные услуги
        completed_services = sum(1 for s in plan.get("services", []) if s.get("status") == "completed")
        total_services = len(plan.get("services", []))
        
        result.append({
            "_id": str(plan["_id"]),
            "status": plan.get("status", "draft"),
            "created_at": plan.get("created_at").isoformat() if plan.get("created_at") else None,
            "approved_at": plan.get("approved_at").isoformat() if plan.get("approved_at") else None,
            "doctor_name": doctor.get("full_name") if doctor else "Не указан",
            "diagnosis": plan.get("diagnosis", ""),
            "total_cost": total_cost,
            "services_count": total_services,
            "completed_count": completed_services,
            "services": plan.get("services", [])
        })
    
    return jsonify(result)

