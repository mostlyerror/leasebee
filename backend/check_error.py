from app.core.database import SessionLocal
from app.models.lease import Lease
from sqlalchemy import desc

db = SessionLocal()
lease = db.query(Lease).order_by(desc(Lease.created_at)).first()
if lease:
    print(f"Latest Lease ID: {lease.id}")
    print(f"Status: {lease.status}")
    if lease.error_message:
        print(f"Error: {lease.error_message}")
    else:
        print("No error message")
else:
    print("No leases found")
db.close()
