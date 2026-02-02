---
hide:
  - navigation
---

# Bennu

**DIY 3D-printed 7" quadcopter for outdoor photogrammetry**

## What is Bennu?

Bennu is an open-source data-acquisition drone designed for aerial photogrammetry and site survey. It captures geotagged aerial images during autonomous survey flights and packages them into signed, versioned mission bundles. Bundles can be processed locally with OpenDroneMap or ingested by an independent geospatial analysis platform.

The project combines a 3D-printed frame with production-grade flight software, giving you a capable survey drone at a fraction of commercial costs (~$650-850).

### Tech Stack

| Component | Choice |
|---|---|
| **Flight Controller** | PX4 v1.16+ on Holybro Pixhawk 6C |
| **Companion Computer** | Raspberry Pi 5 (8GB), Ubuntu 24.04, ROS2 Jazzy |
| **PX4-ROS2 Bridge** | uXRCE-DDS |
| **Camera** | Raspberry Pi HQ Camera (IMX477, 12.3MP) + 6mm CS-mount lens |
| **Processing** | WebODM / OpenDroneMap |

## Getting Started

New to Bennu? Head to the [Tutorials](tutorials/index.md) section for step-by-step build guides that walk you through the entire process from first print to first flight.

## Explore the Docs

<div class="grid cards" markdown>

- :material-school: **[Tutorials](tutorials/index.md)**

    Step-by-step build guides

- :material-wrench: **[How-to Guides](how-to/index.md)**

    Task-oriented recipes

- :material-lightbulb: **[Concepts](concepts/index.md)**

    Architecture and design explanations

- :material-book-open-variant: **[Reference](reference/index.md)**

    Technical specifications and data

- :material-scale-balance: **[Decisions](decisions/index.md)**

    Architecture Decision Records

- :material-post: **[Build Log](blog/index.md)**

    Project journal

</div>
