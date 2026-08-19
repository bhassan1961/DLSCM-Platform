"""EDXL-DE and CAP message generation and parsing."""

import uuid
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone

CAP_NS = "urn:oasis:names:tc:emergency:cap:1.2"
EDXL_NS = "urn:oasis:names:tc:emergency:EDXL:DE:2.0"


def generate_cap_alert(
    title: str,
    description: str,
    severity: str,
    urgency: str = "Immediate",
    certainty: str = "Observed",
    event_type: str = "Met",
    latitude: float | None = None,
    longitude: float | None = None,
    radius_km: float | None = None,
    sender: str = "DLSCM Platform",
    expires_hours: int = 24,
) -> str:
    """Generate a CAP 1.2 alert XML message."""
    now = datetime.now(timezone.utc)
    identifier = f"DLSCM-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"

    severity_map = {
        "minor": "Minor",
        "moderate": "Moderate",
        "severe": "Severe",
        "extreme": "Extreme",
    }
    cap_severity = severity_map.get(severity.lower(), "Moderate")

    alert = ET.Element("alert", xmlns=CAP_NS)
    ET.SubElement(alert, "identifier").text = identifier
    ET.SubElement(alert, "sender").text = sender
    ET.SubElement(alert, "sent").text = now.isoformat()
    ET.SubElement(alert, "status").text = "Actual"
    ET.SubElement(alert, "msgType").text = "Alert"
    ET.SubElement(alert, "scope").text = "Public"

    info = ET.SubElement(alert, "info")
    ET.SubElement(info, "language").text = "en"
    ET.SubElement(info, "category").text = event_type
    ET.SubElement(info, "event").text = title
    ET.SubElement(info, "urgency").text = urgency
    ET.SubElement(info, "severity").text = cap_severity
    ET.SubElement(info, "certainty").text = certainty
    ET.SubElement(info, "headline").text = title
    ET.SubElement(info, "description").text = description
    ET.SubElement(info, "expires").text = (
        now + timedelta(hours=expires_hours)
    ).isoformat()

    if latitude is not None and longitude is not None:
        area = ET.SubElement(info, "area")
        ET.SubElement(
            area, "areaDesc"
        ).text = f"Point at {latitude:.4f}, {longitude:.4f}"
        circle_text = f"{latitude},{longitude} {radius_km or 50}"
        ET.SubElement(area, "circle").text = circle_text

    return ET.tostring(alert, encoding="unicode", xml_declaration=True)


def generate_edxl_de(
    content_xml: str,
    distribution_type: str = "Report",
    sender_id: str = "dlscm@platform.org",
    keywords: list | None = None,
    target_areas: list | None = None,
) -> str:
    """Wrap content in an EDXL-DE 2.0 distribution envelope."""
    now = datetime.now(timezone.utc)
    dist_id = (
        f"DLSCM-EDXL-{now.strftime('%Y%m%dT%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
    )

    root = ET.Element("EDXLDistribution", xmlns=EDXL_NS)
    ET.SubElement(root, "distributionID").text = dist_id
    ET.SubElement(root, "senderID").text = sender_id
    ET.SubElement(root, "dateTimeSent").text = now.isoformat()
    ET.SubElement(root, "distributionStatus").text = "Actual"
    ET.SubElement(root, "distributionType").text = distribution_type
    ET.SubElement(root, "combinedConfidentiality").text = "UNCLASSIFIED"

    if keywords:
        keyword_elem = ET.SubElement(root, "keyword")
        for kw in keywords:
            ET.SubElement(keyword_elem, "value").text = kw

    if target_areas:
        for area in target_areas:
            ta = ET.SubElement(root, "targetArea")
            if "circle" in area:
                ET.SubElement(ta, "circle").text = area["circle"]
            if "country" in area:
                ET.SubElement(ta, "country").text = area["country"]

    content_obj = ET.SubElement(root, "contentObject")
    ET.SubElement(
        content_obj, "contentDescription"
    ).text = f"EDXL-DE wrapped content - {distribution_type}"

    xml_content = ET.SubElement(content_obj, "xmlContent")
    embedded = ET.SubElement(xml_content, "embeddedXMLContent")

    try:
        content_tree = ET.fromstring(content_xml)
        embedded.append(content_tree)
    except ET.ParseError:
        embedded.text = content_xml

    return ET.tostring(root, encoding="unicode", xml_declaration=True)


def parse_edxl_message(xml_text: str) -> dict:
    """Parse an EDXL-DE or CAP message and extract structured data."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as e:
        return {"error": f"Invalid XML: {e!s}"}

    tag = root.tag.split("}")[-1] if "}" in root.tag else root.tag

    if tag == "alert":
        return _parse_cap(root)
    elif tag == "EDXLDistribution":
        return _parse_edxl_de(root)
    else:
        return {
            "error": f"Unknown root element: {tag}",
            "supported": ["alert (CAP)", "EDXLDistribution (EDXL-DE)"],
        }


def _parse_cap(root) -> dict:
    ns = {"cap": CAP_NS}

    def _text(el, path, default=""):
        found = el.find(path, ns) if ns else el.find(path)
        if found is None:
            found = el.find(path)
        return found.text if found is not None and found.text else default

    result = {
        "message_type": "CAP",
        "identifier": _text(root, "identifier") or _text(root, "cap:identifier"),
        "sender": _text(root, "sender") or _text(root, "cap:sender"),
        "sent": _text(root, "sent") or _text(root, "cap:sent"),
        "status": _text(root, "status") or _text(root, "cap:status"),
        "msg_type": _text(root, "msgType") or _text(root, "cap:msgType"),
        "scope": _text(root, "scope") or _text(root, "cap:scope"),
    }

    info = root.find("info") or root.find("cap:info", ns)
    if info is not None:
        result["info"] = {
            "event": _text(info, "event") or _text(info, "cap:event"),
            "urgency": _text(info, "urgency") or _text(info, "cap:urgency"),
            "severity": _text(info, "severity") or _text(info, "cap:severity"),
            "certainty": _text(info, "certainty") or _text(info, "cap:certainty"),
            "headline": _text(info, "headline") or _text(info, "cap:headline"),
            "description": _text(info, "description") or _text(info, "cap:description"),
            "expires": _text(info, "expires") or _text(info, "cap:expires"),
        }

    return result


def _parse_edxl_de(root) -> dict:
    def _text(path, default=""):
        el = root.find(path)
        if el is None:
            for child in root:
                tag = child.tag.split("}")[-1] if "}" in child.tag else child.tag
                if tag == path:
                    return child.text or default
        return el.text if el is not None and el.text else default

    return {
        "message_type": "EDXL-DE",
        "distribution_id": _text("distributionID"),
        "sender_id": _text("senderID"),
        "date_time_sent": _text("dateTimeSent"),
        "distribution_status": _text("distributionStatus"),
        "distribution_type": _text("distributionType"),
        "confidentiality": _text("combinedConfidentiality"),
        "has_content": root.find("contentObject") is not None,
    }
