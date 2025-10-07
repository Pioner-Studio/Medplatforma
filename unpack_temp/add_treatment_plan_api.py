@app.route('/api/patients/<patient_id>/treatment-plans')
@login_required
def api_patient_treatment_plans(patient_id):
    try:
        patient_oid = ObjectId(patient_id)
        plans = list(db.treatment_plans.find({'patient_id': patient_oid}).sort('created_at', -1))
        
        result = []
        for plan in plans:
            doctor = db.users.find_one({'_id': plan.get('doctor_id')})
            result.append({
                'id': str(plan['_id']),
                'status': plan.get('status'),
                'total_amount': plan.get('total_amount', 0),
                'services_count': len(plan.get('services', [])),
                'created_at': plan.get('created_at').strftime('%d.%m.%Y') if plan.get('created_at') else '',
                'doctor_name': doctor.get('full_name', '') if doctor else '',
                'services': plan.get('services', [])
            })
        
        return jsonify({'ok': True, 'plans': result})
    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500
