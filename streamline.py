import numpy as np
from scipy.interpolate import RegularGridInterpolator
from scipy.integrate import solve_ivp

def streamline(X, Y, U, V, start_point, t_max=100000, max_points=10000, method='LSODA',normalize_velocity=False):
    """
    Computes a streamline in both forward and backward directions using SciPy's ODE solver.
    
    Parameters:
    - X, Y: Meshgrid of coordinates.
    - U, V: Velocity field components.
    - start_point: Tuple (x, y) of the seed location.
    - t_max: Maximum integration time.
    - max_points: Maximum number of points in each direction.
    - method: ODE solver method (e.g., 'RK45', 'RK23', 'LSODA').
    - normalize_velocity: Normalizes the interpolated velocity field. This effectivly changes the time integrant to a distance

    Matplotlib streamline seems to use LSODA for integration
    
    Returns:
    - Nx2 NumPy array of (x, y) streamline points, ready for plotting.
    """
    # Create interpolators for velocity field
    U_interp = RegularGridInterpolator((Y[:, 0], X[0, :]), U, bounds_error=False, fill_value=None)
    V_interp = RegularGridInterpolator((Y[:, 0], X[0, :]), V, bounds_error=False, fill_value=None)
    if normalize_velocity:
        normalizer = RegularGridInterpolator((Y[:, 0], X[0, :]), np.sqrt(U**2+V**2), bounds_error=False, fill_value=None)
    else:
        normalizer = lambda xy : 1.0 # always return 1.0

    def velocity_field(t, xy):
        """Velocity field function for ODE solver."""
        x, y = xy
        uv = np.array([U_interp((y, x))/normalizer((y,x)), V_interp((y, x))/normalizer((y,x))])
        return uv if np.all(np.isfinite(uv)) else [0, 0]  # Stop if out of bounds


    # Time evaluation points
    t_eval_fwd = np.linspace(0, t_max, max_points)    # Forward: Increasing time
    t_eval_bwd = np.linspace(0, -t_max, max_points)   # Backward: Decreasing time

    # Forward integration (t = 0 to t_max)
    sol_fwd = solve_ivp(velocity_field, [0, t_max], start_point, method=method, t_eval=t_eval_fwd)
    fwd_points = np.column_stack((sol_fwd.y[0], sol_fwd.y[1]))

    # Backward integration (t = 0 to -t_max)
    sol_bwd = solve_ivp(velocity_field, [0, -t_max], start_point, method=method, t_eval=t_eval_bwd)
    bwd_points = np.column_stack((sol_bwd.y[0], sol_bwd.y[1]))

    # Combine backward and forward paths (excluding duplicate start point)
    streamline_points = np.vstack((bwd_points[::-1], fwd_points[1:]))  # Reverse backward and merge

    return streamline_points  # Nx2 NumPy array
