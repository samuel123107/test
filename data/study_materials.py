study_materials = []

subjects = [
    ("Mathematics","கணிதம்"),
    ("Physics","இயற்பியல்"),
    ("Chemistry","வேதியியல்"),
    ("Biology","உயிரியல்"),
    ("Computer Science","கணினி அறிவியல்"),
    ("Engineering","பொறியியல்"),
    ("Law","சட்டம்"),
    ("Medical Science","மருத்துவ அறிவியல்"),
    ("History","வரலாறு"),
    ("Geography","புவியியல்"),
    ("Economics","பொருளாதாரம்"),
    ("Social Science","சமூக அறிவியல்"),
    ("English Grammar","ஆங்கில இலக்கணம்"),
    ("General Knowledge","பொது அறிவு")
]

for subject_en, subject_ta in subjects:
    for i in range(1, 1801): # 1800 items

        study_materials.append({
            "id": len(study_materials) + 1,
            "title": f"{subject_en} Topic {i}",
            "subject": subject_en,
            "language": "English",
            "content": f"This material explains {subject_en} topic {i}. It includes definitions, formulas, explanations, and examples for students."
        })

        study_materials.append({
            "id": len(study_materials) + 1,
            "title": f"{subject_ta} பாடம் {i}",
            "subject": subject_ta,
            "language": "Tamil",
            "content": f"இந்த பாடத்தில் {subject_ta} தொடர்பான கருத்துகள், விளக்கங்கள் மற்றும் எடுத்துக்காட்டுகள் வழங்கப்படுகின்றன."
        })
