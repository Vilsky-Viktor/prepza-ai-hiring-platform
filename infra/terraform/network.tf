# A private network for the services' outgoing traffic. Calls between services go through it, so
# they arrive as internal although the services only take outside traffic from the load
# balancer; everything else reaches the internet through Cloud NAT.
resource "google_compute_network" "main" {
  name                    = "testee"
  auto_create_subnetworks = false

  depends_on = [google_project_service.apis]
}

resource "google_compute_subnetwork" "run" {
  name                     = "testee-run"
  region                   = var.region
  network                  = google_compute_network.main.id
  ip_cidr_range            = "10.8.0.0/24"
  private_ip_google_access = true
}

resource "google_compute_router" "main" {
  name    = "testee"
  region  = var.region
  network = google_compute_network.main.id
}

# The NAT's one fixed address: the frontend's server-side calls to the API reach the load balancer
# from it, so Cloud Armor's per-IP limit leaves it out (edge_security.tf). One address gives about
# 64,000 ports, far above what this size needs.
resource "google_compute_address" "nat" {
  name       = "testee-nat"
  region     = var.region
  depends_on = [google_project_service.apis]
}

# Each instance gets NAT ports as it needs them: 64 at first, up to 4096. A fixed 64 would cap an
# instance at about 64 connections to one address (Upstash, OpenAI, Resend).
resource "google_compute_router_nat" "main" {
  name                                = "testee"
  router                              = google_compute_router.main.name
  region                              = var.region
  nat_ip_allocate_option              = "MANUAL_ONLY"
  nat_ips                             = [google_compute_address.nat.self_link]
  source_subnetwork_ip_ranges_to_nat  = "ALL_SUBNETWORKS_ALL_IP_RANGES"
  enable_dynamic_port_allocation      = true
  enable_endpoint_independent_mapping = false
  min_ports_per_vm                    = 64
  max_ports_per_vm                    = 4096
}
