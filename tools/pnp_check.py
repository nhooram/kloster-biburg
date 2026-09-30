"""Fit the 2020 photo's camera from known LoD2 corners, then back-solve tower heights."""
import cv2, numpy as np
X_W, X_TW, X_TE = -27.46, -0.95, 7.85; X_TC = (X_TW + X_TE) / 2
pts = {  # model (x,y,z) : photo px  (refs/photos/2020_St_Maria_Biburg.jpg, 1920x1546)
    (X_W, 0, 20.86): (437, 25), (X_W, 4.3, 14.84): (245, 540), (X_W, -4.3, 14.84): (690, 420),
    (X_W, 8.65, 7.3): (88, 1015), (X_W, -8.65, 7.3): (985, 925), (X_W, 0, 0): (480, 1465),
    (X_TW, -4.3, 14.84): (1455, 835), (X_TW, -11.95, 14.84): (1748, 800), (X_TC, -11.95, 20.86): (1780, 570), (X_TE, -11.95, 14.84): (1820, 865),
    (X_TW, -8.65, 7.3): (1615, 1112),
}
P3 = np.array(list(pts), float); P2 = np.array(list(pts.values()), float)
W, H = 1920, 1546
best = None
for f in np.arange(800, 4000, 10):
    K = np.array([[f, 0, W / 2], [0, f, H / 2], [0, 0, 1]])
    ok, rv, tv = cv2.solvePnP(P3, P2, K, None, flags=cv2.SOLVEPNP_ITERATIVE)
    pr, _ = cv2.projectPoints(P3, rv, tv, K, None)
    e = np.sqrt(((pr.reshape(-1, 2) - P2) ** 2).sum(1)).mean()
    if best is None or e < best[0]: best = (e, f, rv, tv, K)
e, f, rv, tv, K = best
print(f"focal {f:.0f}px  mean reproj err {e:.1f}px")
R, _ = cv2.Rodrigues(rv); cam = (-R.T @ tv).ravel(); print("camera pos", cam.round(1))
pr, _ = cv2.projectPoints(P3, rv, tv, K, None)
for p, q, r in zip(P3, P2, pr.reshape(-1, 2)): print(p, q, r.round(0))
# south tower (x 9.4..15.42, y -8.8..-4.3): find z whose projection matches observed eaves / apex pixels
def z_for(x, y, v_obs):
    zs = np.arange(10, 45, 0.02)
    pr, _ = cv2.projectPoints(np.array([[x, y, z] for z in zs]), rv, tv, K, None)
    return zs[np.abs(pr.reshape(-1, 2)[:, 1] - v_obs).argmin()]
print("S tower SW eaves corner z:", z_for(9.4, -8.8, 445))
print("S tower SE eaves corner z:", z_for(15.42, -8.8, 470))
print("S tower helm apex z:", z_for(12.41, -6.55, 205), " ball top", z_for(12.41, -6.55, 180), " cross top", z_for(12.41, -6.55, 130))
print("N tower helm apex z:", z_for(12.41, 6.55, 318), " eaves SW corner", z_for(9.4, 4.3, 500))
