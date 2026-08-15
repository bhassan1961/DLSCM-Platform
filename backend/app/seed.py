import random
from datetime import datetime, timedelta
from app.database import engine, SessionLocal, Base
from app.models import (
    Organization, User, Warehouse, Item, Stock, Disaster,
    SupplyRequest, RequestItem, Alert, Shipment, ShipmentLeg,
    ThreeWEntry, DemandForecast, DonorReport, AfterActionReview,
    SurgeCapacityListing, Scenario,
)

random.seed(42)


def seed_all():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check idempotency
        if db.query(Organization).count() > 0:
            print("Database already seeded. Skipping.")
            return

        # ── Organizations ──────────────────────────────────────────────
        orgs = [
            Organization(name="IFRC", org_type="ngo", country="Switzerland"),
            Organization(name="MSF Logistics", org_type="ngo", country="Belgium"),
            Organization(name="WFP", org_type="un_agency", country="Italy"),
            Organization(name="Kenya Red Cross", org_type="ngo", country="Kenya"),
            Organization(name="DHL Disaster Response", org_type="private", country="Germany"),
        ]
        db.add_all(orgs)
        db.flush()

        # ── Users ──────────────────────────────────────────────────────
        users = [
            User(name="Amina Osei", email="amina.osei@ifrc.org", role="ops_director", organization_id=orgs[0].id),
            User(name="Lars Bergstrom", email="lars.bergstrom@ifrc.org", role="field_coordinator", organization_id=orgs[0].id),
            User(name="Claire Dubois", email="claire.dubois@msf.org", role="supply_manager", organization_id=orgs[1].id),
            User(name="Paolo Rossi", email="paolo.rossi@wfp.org", role="ops_director", organization_id=orgs[2].id),
            User(name="Fatima Njeri", email="fatima.njeri@wfp.org", role="compliance_officer", organization_id=orgs[2].id),
            User(name="James Kamau", email="james.kamau@kenyaredcross.org", role="field_coordinator", organization_id=orgs[3].id),
            User(name="Sarah Wanjiku", email="sarah.wanjiku@kenyaredcross.org", role="supply_manager", organization_id=orgs[3].id),
            User(name="Hans Mueller", email="hans.mueller@dhl.com", role="ops_director", organization_id=orgs[4].id),
        ]
        db.add_all(users)
        db.flush()

        # ── Warehouses ─────────────────────────────────────────────────
        warehouses = [
            Warehouse(name="Nairobi Hub", location="Nairobi, Kenya", latitude=-1.2921, longitude=36.8219, capacity_m3=12000.0, organization_id=orgs[3].id),
            Warehouse(name="Mombasa Port Store", location="Mombasa, Kenya", latitude=-4.0435, longitude=39.6682, capacity_m3=8000.0, organization_id=orgs[3].id),
            Warehouse(name="Amman Regional Depot", location="Amman, Jordan", latitude=31.9454, longitude=35.9284, capacity_m3=15000.0, organization_id=orgs[0].id),
            Warehouse(name="Dhaka Forward Base", location="Dhaka, Bangladesh", latitude=23.8103, longitude=90.4125, capacity_m3=6000.0, organization_id=orgs[2].id),
            Warehouse(name="Dubai Logistics Center", location="Dubai, UAE", latitude=25.2048, longitude=55.2708, capacity_m3=20000.0, organization_id=orgs[4].id),
            Warehouse(name="Addis Ababa Store", location="Addis Ababa, Ethiopia", latitude=9.0250, longitude=38.7469, capacity_m3=9000.0, organization_id=orgs[0].id),
        ]
        db.add_all(warehouses)
        db.flush()

        # ── Items ──────────────────────────────────────────────────────
        items = [
            # Food
            Item(name="High Energy Biscuits (500g)", sku="FOOD-HEB-500", category="food", unit="carton", weight_kg=12.0, volume_m3=0.025),
            Item(name="Plumpy'Nut RUTF (150 sachets)", sku="FOOD-RUTF-150", category="food", unit="carton", weight_kg=13.8, volume_m3=0.030),
            Item(name="Rice (25kg bag)", sku="FOOD-RICE-25K", category="food", unit="bag", weight_kg=25.0, volume_m3=0.040),
            Item(name="Vegetable Oil (5L)", sku="FOOD-OIL-5L", category="food", unit="jerrycan", weight_kg=4.6, volume_m3=0.006),
            # Water
            Item(name="Water Purification Tablets (1000ct)", sku="WAT-PUR-1000", category="water", unit="box", weight_kg=0.5, volume_m3=0.002),
            Item(name="Collapsible Jerry Can (10L)", sku="WAT-JCN-10L", category="water", unit="piece", weight_kg=0.3, volume_m3=0.001),
            Item(name="Gravity Water Filter", sku="WAT-FLT-GRV", category="water", unit="piece", weight_kg=2.5, volume_m3=0.015),
            # Medical
            Item(name="IEHK Basic Unit Kit", sku="MED-IEHK-BAS", category="medical", unit="kit", weight_kg=45.0, volume_m3=0.200),
            Item(name="Oral Rehydration Salts (100 sachets)", sku="MED-ORS-100", category="medical", unit="box", weight_kg=2.1, volume_m3=0.008),
            Item(name="Surgical Supplies Kit", sku="MED-SURG-KIT", category="medical", unit="kit", weight_kg=28.0, volume_m3=0.120),
            # Shelter
            Item(name="Family Tent (16m2)", sku="SHL-TENT-16", category="shelter", unit="piece", weight_kg=55.0, volume_m3=0.250),
            Item(name="Tarpaulin (4x6m)", sku="SHL-TARP-4X6", category="shelter", unit="piece", weight_kg=3.5, volume_m3=0.012),
            Item(name="Thermal Blanket", sku="SHL-BLNK-THR", category="shelter", unit="piece", weight_kg=1.8, volume_m3=0.005),
            # Hygiene
            Item(name="Hygiene Kit (Family)", sku="HYG-KIT-FAM", category="hygiene", unit="kit", weight_kg=5.5, volume_m3=0.020),
            Item(name="Soap Bar (250g, 48-pack)", sku="HYG-SOAP-48", category="hygiene", unit="carton", weight_kg=12.0, volume_m3=0.018),
            Item(name="Menstrual Hygiene Kit", sku="HYG-MHK-001", category="hygiene", unit="kit", weight_kg=1.2, volume_m3=0.008),
            # NFI
            Item(name="Kitchen Set (Family)", sku="NFI-KTCH-FAM", category="nfi", unit="kit", weight_kg=8.5, volume_m3=0.040),
            Item(name="Solar Lantern", sku="NFI-SOLR-LNT", category="nfi", unit="piece", weight_kg=0.4, volume_m3=0.002),
            Item(name="Sleeping Mat", sku="NFI-SMAT-001", category="nfi", unit="piece", weight_kg=1.5, volume_m3=0.010),
            Item(name="Mosquito Net (LLIN)", sku="NFI-MNET-LLI", category="nfi", unit="piece", weight_kg=0.5, volume_m3=0.003),
        ]
        db.add_all(items)
        db.flush()

        # ── Stock ──────────────────────────────────────────────────────
        now = datetime.utcnow()
        for wh in warehouses:
            selected_items = random.sample(items, random.randint(10, 18))
            for item in selected_items:
                lot = f"LOT-{wh.id:02d}-{item.id:03d}-{random.randint(1000,9999)}"
                exp = now + timedelta(days=random.randint(90, 730))
                stock = Stock(
                    warehouse_id=wh.id,
                    item_id=item.id,
                    quantity=random.randint(50, 5000),
                    lot_number=lot,
                    expiry_date=exp,
                )
                db.add(stock)
        db.flush()

        # ── Disasters ─────────────────────────────────────────────────
        disasters = [
            Disaster(
                name="Turkana Drought", disaster_type="drought", severity="major",
                status="active", country="Kenya", region="Turkana County",
                latitude=3.3122, longitude=35.5658, affected_population=850000,
                start_date=now - timedelta(days=120),
                description="Prolonged drought affecting pastoralist communities in Turkana County. Three consecutive failed rainy seasons have decimated livestock and exhausted water sources.",
            ),
            Disaster(
                name="Cox's Bazar Monsoon Flooding", disaster_type="flood", severity="catastrophic",
                status="active", country="Bangladesh", region="Cox's Bazar",
                latitude=21.4272, longitude=92.0058, affected_population=1200000,
                start_date=now - timedelta(days=45),
                description="Severe monsoon flooding in Cox's Bazar affecting Rohingya refugee camps and host communities. Landslides have destroyed shelters and infrastructure.",
            ),
            Disaster(
                name="Aleppo Earthquake Aftermath", disaster_type="earthquake", severity="catastrophic",
                status="active", country="Syria", region="Aleppo Governorate",
                latitude=36.2021, longitude=37.1343, affected_population=2100000,
                start_date=now - timedelta(days=200),
                description="Ongoing recovery from the 7.8 magnitude earthquake. Thousands still displaced with critical infrastructure damage across northern Syria.",
            ),
            Disaster(
                name="Mozambique Cyclone Frieda", disaster_type="cyclone", severity="major",
                status="active", country="Mozambique", region="Sofala Province",
                latitude=-19.8436, longitude=34.8389, affected_population=520000,
                start_date=now - timedelta(days=18),
                description="Category 4 cyclone making landfall near Beira. Widespread destruction of housing, power lines, and agricultural land. Flooding in low-lying areas.",
            ),
        ]
        db.add_all(disasters)
        db.flush()

        # ── Supply Requests ────────────────────────────────────────────
        request_data = [
            ("Emergency food rations for Turkana camps", "critical", 0, 5, 3.3122, 35.5658, "Turkana Camp Alpha", "approved"),
            ("Medical supplies for Lodwar clinic", "high", 0, 0, 3.1191, 35.5970, "Lodwar Health Center", "dispatched"),
            ("Shelter materials for Cox's Bazar Camp 4", "critical", 1, 1, 21.1800, 92.1500, "Camp 4 Extension", "sourcing"),
            ("Water purification for monsoon-affected areas", "high", 1, 2, 21.4272, 92.0058, "Cox's Bazar Central", "pending"),
            ("IEHK kits for Aleppo field hospitals", "critical", 2, 3, 36.2021, 37.1343, "Aleppo Field Hospital 3", "approved"),
            ("Hygiene kits for displaced families", "medium", 2, 0, 36.1900, 37.1600, "Al-Bab IDP Camp", "delivered"),
            ("NFI distribution for Beira suburbs", "high", 3, 5, -19.8436, 34.8389, "Beira Distribution Point", "pending"),
            ("Emergency tents for Sofala Province", "critical", 3, 6, -19.7800, 34.8600, "Dondo Camp", "approved"),
            ("Therapeutic food for malnourished children", "high", 0, 4, 3.5200, 35.8500, "Kakuma Nutrition Center", "sourcing"),
            ("Blankets and sleeping mats for winter prep", "medium", 2, 0, 36.3400, 36.5900, "Idlib Transit Camp", "pending"),
        ]
        supply_requests = []
        for title, priority, d_idx, u_idx, lat, lng, dest, status in request_data:
            sr = SupplyRequest(
                title=title, status=status, priority=priority,
                disaster_id=disasters[d_idx].id, requester_id=users[u_idx].id,
                destination_lat=lat, destination_lng=lng, destination_name=dest,
                notes=f"Requested via field assessment on {(now - timedelta(days=random.randint(1,30))).strftime('%Y-%m-%d')}",
                created_at=now - timedelta(days=random.randint(1, 30)),
            )
            db.add(sr)
            db.flush()
            supply_requests.append(sr)

            # Add 2-6 request items
            num_items = random.randint(2, 6)
            selected = random.sample(items, num_items)
            for item in selected:
                qty = random.randint(50, 2000)
                fulfilled = 0
                if status in ("dispatched", "delivered"):
                    fulfilled = qty
                elif status == "sourcing":
                    fulfilled = int(qty * random.uniform(0.3, 0.7))
                ri = RequestItem(
                    request_id=sr.id, item_id=item.id,
                    quantity_requested=qty, quantity_fulfilled=fulfilled,
                )
                db.add(ri)
        db.flush()

        # ── Shipments ──────────────────────────────────────────────────
        shipment_data = [
            ("SHP-20250801", supply_requests[0].id, warehouses[0].id, "in_transit", "road", "Kenya Red Cross Fleet", -1.8, 36.2, 8),
            ("SHP-20250802", supply_requests[1].id, warehouses[0].id, "delivered", "air", "UNHAS", 3.1191, 35.5970, 0),
            ("SHP-20250803", supply_requests[2].id, warehouses[3].id, "preparing", "road", "Local Transport Co.", 23.8103, 90.4125, 24),
            ("SHP-20250804", supply_requests[4].id, warehouses[2].id, "in_transit", "road", "ICRC Convoy", 34.5, 36.8, 36),
            ("SHP-20250805", supply_requests[7].id, warehouses[4].id, "in_transit", "air", "DHL Express", 5.0, 45.0, 18),
        ]
        shipments = []
        for tid, rid, wid, status, mode, carrier, clat, clng, eta_h in shipment_data:
            s = Shipment(
                tracking_id=tid, request_id=rid, origin_warehouse_id=wid,
                status=status, transport_mode=mode, carrier=carrier,
                current_lat=clat, current_lng=clng,
                eta=now + timedelta(hours=eta_h) if eta_h > 0 else None,
                departed_at=now - timedelta(hours=random.randint(6, 48)) if status != "preparing" else None,
                delivered_at=now - timedelta(hours=6) if status == "delivered" else None,
                created_at=now - timedelta(days=random.randint(1, 10)),
            )
            db.add(s)
            db.flush()
            shipments.append(s)

        # Shipment legs
        leg_data = [
            (shipments[0].id, [(-1.2921, 36.8219, 0.5, 35.5, "road", 420, 9.3), (0.5, 35.5, 3.3122, 35.5658, "road", 310, 6.9)]),
            (shipments[1].id, [(-1.2921, 36.8219, 3.1191, 35.5970, "air", 530, 0.8)]),
            (shipments[3].id, [(31.9454, 35.9284, 34.5, 36.8, "road", 290, 6.4), (34.5, 36.8, 36.2021, 37.1343, "road", 195, 4.3)]),
            (shipments[4].id, [(25.2048, 55.2708, 5.0, 45.0, "air", 2400, 3.7), (5.0, 45.0, -19.8436, 34.8389, "air", 2900, 4.5)]),
        ]
        for sid, legs in leg_data:
            for i, (flat, flng, tlat, tlng, mode, dist, dur) in enumerate(legs):
                leg = ShipmentLeg(
                    shipment_id=sid, leg_order=i + 1,
                    from_lat=flat, from_lng=flng, to_lat=tlat, to_lng=tlng,
                    mode=mode, distance_km=dist, duration_hours=dur,
                )
                db.add(leg)
        db.flush()

        # ── Alerts ─────────────────────────────────────────────────────
        alerts = [
            Alert(source="cap", alert_type="meteorological", severity="extreme", title="Severe Cyclone Warning - Mozambique Channel", description="Tropical Cyclone Frieda intensifying. Expected landfall within 24 hours with sustained winds exceeding 200 km/h. Storm surge of 3-5 meters expected along Sofala coast.", latitude=-19.5, longitude=35.2, issued_at=now - timedelta(days=19), expires_at=now - timedelta(days=17), status="expired", raw_message='<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"><identifier>MOZ-20250727-001</identifier></alert>'),
            Alert(source="cap", alert_type="hydrological", severity="severe", title="Flash Flood Warning - Cox's Bazar District", description="Heavy monsoon rainfall expected to produce flash flooding in low-lying areas of Cox's Bazar. Refugee camps on hillsides at risk of landslides.", latitude=21.4272, longitude=92.0058, issued_at=now - timedelta(days=2), expires_at=now + timedelta(days=1), status="active", raw_message='<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"><identifier>BGD-20250813-003</identifier></alert>'),
            Alert(source="edxl", alert_type="seismic", severity="moderate", title="Aftershock Advisory - Northern Syria", description="Moderate aftershock activity continuing in Aleppo region. M4.2 recorded at 03:41 UTC. Buildings weakened by previous earthquake may be at risk of collapse.", latitude=36.2021, longitude=37.1343, issued_at=now - timedelta(hours=18), expires_at=now + timedelta(hours=48), status="active", raw_message='<EDXLDistribution><distributionID>SYR-AFT-20250814</distributionID></EDXLDistribution>'),
            Alert(source="manual", alert_type="security", severity="severe", title="Access Restriction - Road to Turkana", description="Armed group activity reported along the A1 highway between Lodwar and Kakuma. Humanitarian convoys advised to travel in coordinated groups with security escort.", latitude=3.2, longitude=35.6, issued_at=now - timedelta(days=5), expires_at=now + timedelta(days=2), status="active"),
            Alert(source="cap", alert_type="meteorological", severity="extreme", title="Drought Emergency Declaration - Horn of Africa", description="Fourth consecutive below-normal rainy season confirmed. Acute food insecurity affecting 23 million people across Kenya, Ethiopia, and Somalia. IPC Phase 4 conditions in multiple counties.", latitude=2.0, longitude=38.0, issued_at=now - timedelta(days=60), expires_at=now + timedelta(days=30), status="active", raw_message='<alert xmlns="urn:oasis:names:tc:emergency:cap:1.2"><identifier>HOA-DROUGHT-2025</identifier></alert>'),
            Alert(source="edxl", alert_type="health", severity="severe", title="Cholera Outbreak Alert - Beira, Mozambique", description="Rising cholera cases reported in flood-affected areas of Beira. 342 suspected cases in the past 72 hours. Oral rehydration points being established.", latitude=-19.8436, longitude=34.8389, issued_at=now - timedelta(days=3), expires_at=now + timedelta(days=14), status="active", raw_message='<EDXLDistribution><distributionID>MOZ-CHOL-20250812</distributionID></EDXLDistribution>'),
            Alert(source="manual", alert_type="logistics", severity="moderate", title="Port Congestion - Mombasa", description="Significant delays at Mombasa port due to increased humanitarian cargo volume. Average clearance time increased to 8 days. Alternative routing via Dar es Salaam recommended.", latitude=-4.0435, longitude=39.6682, issued_at=now - timedelta(days=7), expires_at=now + timedelta(days=7), status="acknowledged"),
            Alert(source="cap", alert_type="meteorological", severity="minor", title="Heat Wave Advisory - Jordan Valley", description="Temperatures expected to exceed 45C in the Jordan Valley for the next 5 days. Warehouse temperature monitoring recommended for heat-sensitive medical supplies.", latitude=31.9454, longitude=35.9284, issued_at=now - timedelta(days=1), expires_at=now + timedelta(days=5), status="active"),
        ]
        db.add_all(alerts)
        db.flush()

        # ── 3W Entries ─────────────────────────────────────────────────
        threew_data = [
            (orgs[2].id, disasters[0].id, "food_distribution", "Turkana South", 3.1, 35.6, 45000, -90, None, "active"),
            (orgs[0].id, disasters[0].id, "water_sanitation", "Lodwar Town", 3.1191, 35.5970, 28000, -60, None, "active"),
            (orgs[3].id, disasters[0].id, "medical_services", "Kakuma", 3.7, 34.8, 62000, -100, None, "active"),
            (orgs[1].id, disasters[1].id, "medical_services", "Camp 12, Cox's Bazar", 21.2, 92.05, 35000, -40, None, "active"),
            (orgs[2].id, disasters[1].id, "food_distribution", "Teknaf", 20.85, 92.3, 120000, -44, None, "active"),
            (orgs[0].id, disasters[1].id, "shelter_provision", "Camp 4 Extension", 21.18, 92.15, 18000, -30, None, "active"),
            (orgs[0].id, disasters[2].id, "shelter_provision", "Aleppo City", 36.2, 37.15, 85000, -180, None, "active"),
            (orgs[1].id, disasters[2].id, "medical_services", "Aleppo Hospital Complex", 36.21, 37.13, 150000, -190, None, "active"),
            (orgs[2].id, disasters[2].id, "logistics", "Aleppo Logistics Base", 36.19, 37.16, 0, -150, None, "active"),
            (orgs[4].id, disasters[2].id, "logistics", "Gaziantep Cross-border Hub", 37.06, 37.38, 0, -185, None, "active"),
            (orgs[0].id, disasters[3].id, "shelter_provision", "Beira Suburbs", -19.84, 34.84, 32000, -16, None, "active"),
            (orgs[2].id, disasters[3].id, "food_distribution", "Dondo District", -19.6, 34.74, 55000, -14, None, "active"),
            (orgs[1].id, disasters[3].id, "water_sanitation", "Beira Central", -19.83, 34.87, 41000, -15, None, "active"),
            (orgs[3].id, disasters[0].id, "protection", "Turkana North", 3.5, 35.9, 22000, -80, None, "active"),
            (orgs[4].id, disasters[3].id, "logistics", "Beira Airport Hub", -19.79, 34.91, 0, -17, None, "active"),
        ]
        for oid, did, activity, loc, lat, lng, ben, start_offset, end_offset, status in threew_data:
            entry = ThreeWEntry(
                organization_id=oid, disaster_id=did, activity=activity,
                location=loc, latitude=lat, longitude=lng, beneficiaries=ben,
                start_date=now + timedelta(days=start_offset),
                end_date=now + timedelta(days=end_offset) if end_offset else None,
                status=status,
            )
            db.add(entry)
        db.flush()

        # ── Surge Capacity Marketplace ─────────────────────────────────
        surge_data = [
            (orgs[4].id, "warehouse_space", "Temperature-Controlled Storage - Dubai", "5000 m3 of climate-controlled warehouse space available near Dubai airport for emergency pre-positioning.", 5000, "m3", "Dubai, UAE", 25.2048, 55.2708),
            (orgs[4].id, "transport", "Dedicated Air Cargo - B747F", "Boeing 747 freighter available for emergency deployment. Capacity 120 tonnes. Based in Leipzig.", 120, "tonnes", "Leipzig, Germany", 51.4236, 12.2364),
            (orgs[3].id, "personnel", "Emergency Response Team - East Africa", "10-person emergency response team with logistics, WASH, and health expertise. Deployable within 48 hours.", 10, "persons", "Nairobi, Kenya", -1.2921, 36.8219),
            (orgs[0].id, "warehouse_space", "Overflow Storage - Amman", "3000 m3 overflow storage available at Amman Regional Depot for Syria response surge.", 3000, "m3", "Amman, Jordan", 31.9454, 35.9284),
            (orgs[1].id, "transport", "Refrigerated Truck Fleet - Bangladesh", "4 refrigerated trucks for medical supply transport in Cox's Bazar region.", 4, "vehicles", "Chittagong, Bangladesh", 22.3569, 91.7832),
            (orgs[2].id, "personnel", "Supply Chain Specialists", "3 senior supply chain specialists available for 90-day surge deployment to any WFP operation.", 3, "persons", "Rome, Italy", 41.8967, 12.4822),
        ]
        for oid, ltype, title, desc, cap, unit, loc, lat, lng in surge_data:
            listing = SurgeCapacityListing(
                organization_id=oid, listing_type=ltype, title=title,
                description=desc, capacity_value=cap, capacity_unit=unit,
                location=loc, latitude=lat, longitude=lng,
                available_from=now - timedelta(days=random.randint(1, 30)),
                available_until=now + timedelta(days=random.randint(30, 180)),
                status="available",
            )
            db.add(listing)
        db.flush()

        db.commit()
        print("Seed data created successfully.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_all()
