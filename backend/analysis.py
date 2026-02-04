import numpy as np
from sklearn.cluster import DBSCAN
from shapely.geometry import Point, MultiPoint, Polygon
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import models
from geoalchemy2.shape import to_shape

def detect_coverage_holes(db: Session):
    # SRS 7.1: Fetch Poor Points (RSRP < -110) from last 24 hours
    # Note: Using a wider window for demo purposes if data is sparse
    cutoff_time = datetime.now() - timedelta(hours=24)
    
    poor_points_query = db.query(models.NetworkMeasurement).filter(
        models.NetworkMeasurement.rsrp < -110,
        models.NetworkMeasurement.recorded_at > cutoff_time
    ).all()

    if len(poor_points_query) < 5:
        print("Creating holes: Not enough data points (< 5)")
        return []

    # Extract coordinates for DBSCAN
    coords = []
    for p in poor_points_query:
        pt = to_shape(p.location)
        coords.append([pt.x, pt.y]) # Lon, Lat
    
    X = np.array(coords)

    # SRS 7.1: Configure DBSCAN (eps ~ 50m). 
    # 1 degree lat ~ 111km. 50m = 0.05km. 
    # 0.05 / 111 = 0.00045 degrees. Let's use 0.0005.
    dbscan = DBSCAN(eps=0.0005, min_samples=5).fit(X)
    
    unique_labels = set(dbscan.labels_)
    holes = []

    for label in unique_labels:
        if label == -1: 
            continue # Noise

        # Get points belonging to this cluster
        class_member_mask = (dbscan.labels_ == label)
        cluster_points = X[class_member_mask]

        if len(cluster_points) < 3:
            continue # Needs at least 3 points for a polygon

        # Create Convex Hull
        points = [Point(xy) for xy in cluster_points]
        multipoint = MultiPoint(points)
        hull = multipoint.convex_hull
        
        # Calculate Avg RSRP for severity
        # Map original query back to these points (simplified for now)
        # In a real system, we'd join back by ID.
        # Here we just assume accurate mapping or re-query.
        
        # Calculate centroids/severity
        # Severity = Mean RSRP of points in cluster
        # Optimziation: we have indices in X corresponding to poor_points_query list index?
        # Yes, order is preserved.
        
        cluster_indices = np.where(class_member_mask)[0]
        cluster_rsrps = [poor_points_query[i].rsrp for i in cluster_indices]
        avg_rsrp = sum(cluster_rsrps) / len(cluster_rsrps)

        holes.append({
            "geometry": hull, # Shapely Polygon
            "severity": avg_rsrp,
            "count": len(cluster_points)
        })

    return holes
