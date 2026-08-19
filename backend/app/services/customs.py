from datetime import datetime, timezone

HUMANITARIAN_EXEMPTIONS = {
    "KE": {"name": "Kenya", "exemption": True, "notes": "VAT exempt under Humanitarian Aid Act 2017", "required_docs": ["waybill", "donation_certificate"]},
    "BD": {"name": "Bangladesh", "exemption": True, "notes": "Duty-free under NGOAB registration", "required_docs": ["waybill", "ngoab_clearance", "packing_list"]},
    "SY": {"name": "Syria", "exemption": True, "notes": "Cross-border via UN Resolution 2585 mechanism", "required_docs": ["un_authorization", "waybill", "manifest"]},
    "JO": {"name": "Jordan", "exemption": True, "notes": "Exempt under framework agreement with MoPIC", "required_docs": ["waybill", "mopic_letter"]},
    "MZ": {"name": "Mozambique", "exemption": True, "notes": "Emergency exemption granted during cyclone response", "required_docs": ["waybill", "ingc_authorization"]},
    "ET": {"name": "Ethiopia", "exemption": True, "notes": "NGO imports exempt under Charities Proclamation", "required_docs": ["waybill", "charity_registration"]},
    "AE": {"name": "UAE", "exemption": False, "notes": "Standard customs procedures apply. IHC free zone available.", "required_docs": ["commercial_invoice", "waybill", "packing_list", "certificate_of_origin"]},
    "DE": {"name": "Germany", "exemption": False, "notes": "EU customs procedures. ATA Carnet available for temporary imports.", "required_docs": ["commercial_invoice", "waybill", "eur1_certificate"]},
}

COUNTRY_CODE_MAP = {
    "kenya": "KE", "bangladesh": "BD", "syria": "SY", "jordan": "JO",
    "mozambique": "MZ", "ethiopia": "ET", "uae": "AE", "germany": "DE",
    "switzerland": "CH", "belgium": "BE", "italy": "IT", "china": "CN",
}


def get_country_code(country_name: str) -> str:
    return COUNTRY_CODE_MAP.get(country_name.lower(), country_name.upper()[:2])


def generate_customs_docs(
    shipment_tracking_id: str,
    origin_country: str,
    destination_country: str,
    items: list,
    organization_name: str,
    transport_mode: str,
) -> dict:
    dest_code = get_country_code(destination_country)
    origin_code = get_country_code(origin_country)
    exemption_info = HUMANITARIAN_EXEMPTIONS.get(dest_code, {})

    now = datetime.now(timezone.utc)

    waybill = {
        "document_type": "waybill",
        "document_number": f"WB-{shipment_tracking_id}",
        "issued_date": now.isoformat(),
        "shipper": organization_name,
        "consignee": f"Field Operations - {destination_country}",
        "origin": origin_country,
        "destination": destination_country,
        "transport_mode": transport_mode,
        "items": items,
        "total_packages": sum(i.get("quantity", 1) for i in items),
        "declared_value": "Humanitarian aid - no commercial value",
    }

    packing_list = {
        "document_type": "packing_list",
        "document_number": f"PL-{shipment_tracking_id}",
        "issued_date": now.isoformat(),
        "items": [
            {
                "description": i.get("name", "Humanitarian supplies"),
                "quantity": i.get("quantity", 1),
                "unit": i.get("unit", "pieces"),
                "weight_kg": i.get("weight_kg", 0) * i.get("quantity", 1),
                "hs_code": _get_hs_code(i.get("category", "general")),
            }
            for i in items
        ],
    }

    donation_cert = {
        "document_type": "donation_certificate",
        "document_number": f"DC-{shipment_tracking_id}",
        "issued_date": now.isoformat(),
        "donor_organization": organization_name,
        "purpose": "Humanitarian assistance / disaster relief",
        "declaration": "These goods are donated free of charge for humanitarian purposes and have no commercial value.",
    }

    return {
        "shipment_tracking_id": shipment_tracking_id,
        "origin_country": {"code": origin_code, "name": origin_country},
        "destination_country": {"code": dest_code, "name": destination_country},
        "exemption_available": exemption_info.get("exemption", False),
        "exemption_notes": exemption_info.get("notes", "No specific exemption data available"),
        "required_documents": exemption_info.get("required_docs", ["waybill", "packing_list"]),
        "generated_documents": {
            "waybill": waybill,
            "packing_list": packing_list,
            "donation_certificate": donation_cert,
        },
        "generated_at": now.isoformat(),
    }


def _get_hs_code(category: str) -> str:
    hs_codes = {
        "food": "2106.90",
        "water": "8421.21",
        "medical": "3004.90",
        "shelter": "6306.29",
        "hygiene": "3401.19",
        "nfi": "9403.70",
        "general": "9898.00",
    }
    return hs_codes.get(category, "9898.00")
