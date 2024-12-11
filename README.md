# 3D Meteorite & Impact Crater Viewer 🌠

An interactive 3D visualization of global meteorite specimens and Earth impact craters using CesiumJS.
Initially intended as a testbed for AI coding performance (OpenAI o1-preview), it quickly ballooned to include the following functionality.

## 🌟 Features

- 🌍 **Interactive 3D globe visualization**
- 🔄 **Navigation:** Use mouse or touch controls to rotate, zoom, and pan around the globe.
- 🔍 **Search:** Fly to a specific location using the search bar in the Options menu.
- ⚙️ **Filters:** Adjust filters like year, mass, diameter, age, class, and target rock type in the Options menu to refine the displayed data. Click each slider value to manually set your own limits.
- 👁️ **Show/Hide Data:** Toggle meteorites and impact craters visibility using the checkboxes in the Options menu.
- 📜 **Legends:** View legends for meteorite and crater color schemes in the Key menu to understand data representation. Change the color scheme to suit you, including colourblind-friendly options.
- 🔗 **Clustering:** Enable or disable clustering of meteorite markers to manage display density at different zoom levels. This feature improves performance on mobile devices, so is on by default.
- 🏆 **Top Bars:** Explore top meteorites (by mass) and impact craters (by diameter) at the bottom of the screen. Click to fly to their locations.
- 📂 **View All:** Access full lists of meteorites and craters by clicking "View All". See more information on them by following the links to [MetBull](https://www.lpi.usra.edu/meteor/metbull.php) or the [Impact Crater Database](https://impact-craters.com/).
- 📋 **Details:** Tap/hover on any meteorite or crater to view detailed information in a tooltip. Double click it to see its table entry.
- 🔄 **Reset Filters:** Quickly reset all filters to default settings using the "Reset Filters" button.
- 🎨 **Reset Color Schemes:** Reset the color schemes for meteorites and impact craters to default settings using the "Reset Color Schemes" button in the Key menu.

## 📊 Data Sources

- 🌠 [NASA Meteorite Landings Dataset](https://data.nasa.gov/Space-Science/Meteorite-Landings/gh4g-9sfh)
- 💥 Earth Impact Crater data from [Kenkmann 2021](https://doi.org/10.1111/maps.13657) via [Dr. Matthias Ebert](https://impact-craters.com/).

This application utilizes **CesiumJS** for 3D globe visualization.

## 🚀 Quick Start

1. Access the webapp via [this link](https://impact.arijguest.com).

## 🛠️ Improvements
The current codebase is shoddy at best and needs refactoring & efficiency improvements beyond my abilities. If you'd like to make improvements, please feel free - you'd be doing me a huge favour!

## 📜 License

This project is licensed under the [CC-BY 4.0 License](https://creativecommons.org/licenses/by/4.0/).
