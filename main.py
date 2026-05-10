from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import uvicorn

app = FastAPI(
    title="Mechanical Unit Converter & Material Density Checker API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Material density database (kg/m³)
MATERIAL_DENSITIES = {
    "metals": {
        "steel_mild": 7850, "steel_stainless_304": 7930, "steel_stainless_316": 8000,
        "steel_tool": 7810, "cast_iron": 7200, "aluminum_6061": 2700,
        "aluminum_7075": 2810, "aluminum_cast": 2680, "copper": 8960,
        "brass": 8730, "bronze": 8800, "zinc": 7140, "titanium": 4500,
        "titanium_ti6al4v": 4430, "nickel": 8908, "magnesium": 1740,
        "lead": 11340, "tungsten": 19300, "gold": 19320, "silver": 10490,
        "platinum": 21450, "tin": 7310, "zirconium": 6510, "cobalt": 8900,
        "molybdenum": 10280, "inconel_625": 8440, "inconel_718": 8190,
        "monel_400": 8800, "hastelloy_c276": 8890
    },
    "polymers": {
        "abs": 1050, "pla": 1240, "nylon_6": 1140, "nylon_66": 1150,
        "polyethylene_hd": 950, "polyethylene_ld": 920, "polypropylene": 900,
        "polystyrene": 1050, "pvc_rigid": 1400, "pvc_flexible": 1250,
        "acrylic_pmma": 1190, "polycarbonate": 1200, "pet": 1380,
        "ptfe_teflon": 2200, "peek": 1320, "epoxy_resin": 1200,
        "polyurethane_flexible": 1200, "polyurethane_rigid": 1240,
        "silicone": 1200, "rubber_natural": 920, "rubber_neoprene": 1230,
        "rubber_nitrile": 1000
    },
    "ceramics_glasses": {
        "alumina": 3950, "silicon_carbide": 3210, "silicon_nitride": 3250,
        "zirconia": 6050, "boron_carbide": 2520, "glass_soda_lime": 2500,
        "glass_borosilicate": 2230, "glass_quartz": 2200, "glass_tempered": 2520,
        "porcelain": 2400, "graphite": 2250, "diamond": 3510
    },
    "composites": {
        "carbon_fiber": 1600, "glass_fiber_gfrp": 2000, "kevlar": 1440,
        "wood_plywood": 600, "wood_oak": 750, "wood_pine": 500,
        "wood_balsa": 150, "wood_mdf": 700, "concrete": 2400,
        "concrete_reinforced": 2500, "asphalt": 2300, "brick": 1900,
        "granite": 2700, "marble": 2600, "sandstone": 2300, "limestone": 2600
    },
    "liquids": {
        "water_4c": 1000, "water_20c": 998, "water_100c": 958,
        "seawater": 1025, "oil_engine_sae10": 875, "oil_engine_sae30": 890,
        "oil_engine_sae40": 900, "gasoline": 720, "diesel": 830,
        "ethanol": 789, "methanol": 791, "glycerin": 1260, "mercury": 13593,
        "sulfuric_acid": 1840, "hydrochloric_acid": 1180, "nitric_acid": 1500,
        "acetone": 791, "brake_fluid": 1040
    },
    "gases": {
        "air_20c": 1.204, "air_0c": 1.293, "helium": 0.179,
        "hydrogen": 0.090, "nitrogen": 1.251, "oxygen": 1.429,
        "carbon_dioxide": 1.977, "methane": 0.717, "propane": 2.009,
        "butane": 2.703, "steam_100c": 0.598
    }
}

# Unit conversion factors (to SI units)
CONVERSION_FACTORS = {
    "length": {"meter": 1.0, "kilometer": 1000.0, "centimeter": 0.01, "millimeter": 0.001, "inch": 0.0254, "foot": 0.3048, "yard": 0.9144, "mile": 1609.344},
    "mass": {"kilogram": 1.0, "gram": 0.001, "metric_ton": 1000.0, "pound": 0.453592, "ounce": 0.0283495},
    "force": {"newton": 1.0, "kilonewton": 1000.0, "pound_force": 4.44822, "kilogram_force": 9.80665},
    "pressure": {"pascal": 1.0, "kilopascal": 1000.0, "megapascal": 1e6, "bar": 100000.0, "atmosphere": 101325.0, "psi": 6894.76},
    "energy": {"joule": 1.0, "kilojoule": 1000.0, "calorie": 4.184, "kilocalorie": 4184.0, "btu": 1055.06},
    "power": {"watt": 1.0, "kilowatt": 1000.0, "horsepower": 745.7},
    "velocity": {"meter_per_second": 1.0, "kilometer_per_hour": 0.277778, "mile_per_hour": 0.44704, "knot": 0.514444},
    "area": {"square_meter": 1.0, "square_kilometer": 1e6, "hectare": 10000.0, "square_foot": 0.092903, "square_inch": 0.00064516},
    "volume": {"cubic_meter": 1.0, "liter": 0.001, "milliliter": 1e-6, "gallon_us": 0.00378541, "cubic_foot": 0.0283168},
    "density": {"kg_per_m3": 1.0, "g_per_cm3": 1000.0, "lb_per_ft3": 16.0185},
    "temperature": "special",
    "torque": {"newton_meter": 1.0, "pound_force_foot": 1.35582, "pound_force_inch": 0.112985},
    "stress": {"pascal": 1.0, "megapascal": 1e6, "gigapascal": 1e9, "psi": 6894.76, "ksi": 6894760, "bar": 100000}
}

class ConversionRequest(BaseModel):
    category: str
    value: float
    from_unit: str
    to_unit: str

class MassCalculationRequest(BaseModel):
    material: str
    volume: float
    volume_unit: str = "cubic_meter"
    mass_unit: str = "kilogram"

def convert_temperature(value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == "celsius": celsius = value
    elif from_unit == "fahrenheit": celsius = (value - 32) * 5/9
    elif from_unit == "kelvin": celsius = value - 273.15
    else: raise ValueError(f"Unknown unit: {from_unit}")
    
    if to_unit == "celsius": return celsius
    elif to_unit == "fahrenheit": return (celsius * 9/5) + 32
    elif to_unit == "kelvin": return celsius + 273.15
    else: raise ValueError(f"Unknown unit: {to_unit}")

def search_materials(query: str, category: Optional[str] = None) -> List[Dict]:
    results = []
    search_term = query.lower()
    categories_to_search = [category] if category else MATERIAL_DENSITIES.keys()
    for cat in categories_to_search:
        if cat in MATERIAL_DENSITIES:
            for material, density in MATERIAL_DENSITIES[cat].items():
                if search_term in material.lower():
                    results.append({
                        "material": material,
                        "category": cat,
                        "density_kg_m3": density,
                        "display_name": material.replace("_", " ").title()
                    })
    return results

@app.get("/")
async def root():
    return {"message": "API is running", "version": "1.0.0"}

@app.get("/categories")
async def get_categories():
    categories = {}
    for category, units in CONVERSION_FACTORS.items():
        if units != "special":
            categories[category] = list(units.keys())
        else:
            categories[category] = ["celsius", "fahrenheit", "kelvin"]
    return {"categories": categories, "available_categories": list(CONVERSION_FACTORS.keys())}

@app.post("/convert")
async def convert_units(request: ConversionRequest):
    try:
        if request.category not in CONVERSION_FACTORS:
            raise HTTPException(status_code=400, detail=f"Category '{request.category}' not found")
        
        if request.category == "temperature":
            result = convert_temperature(request.value, request.from_unit, request.to_unit)
            return {"input": request.dict(), "result": result}
        
        units = CONVERSION_FACTORS[request.category]
        if request.from_unit not in units:
            raise HTTPException(status_code=400, detail=f"From unit '{request.from_unit}' not found")
        if request.to_unit not in units:
            raise HTTPException(status_code=400, detail=f"To unit '{request.to_unit}' not found")
        
        base_value = request.value * units[request.from_unit]
        result = base_value / units[request.to_unit]
        
        return {
            "input": {"value": request.value, "from_unit": request.from_unit, "to_unit": request.to_unit, "category": request.category},
            "result": result,
            "conversion_factor": units[request.from_unit] / units[request.to_unit]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/convert")
async def convert_units_get(category: str, value: float, from_unit: str, to_unit: str):
    request = ConversionRequest(category=category, value=value, from_unit=from_unit, to_unit=to_unit)
    return await convert_units(request)

@app.get("/materials")
async def get_all_materials(category: Optional[str] = None, search: Optional[str] = None):
    if search:
        return {"materials": search_materials(search, category)}
    if category:
        if category not in MATERIAL_DENSITIES:
            raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
        return {"category": category, "materials": MATERIAL_DENSITIES[category]}
    return {"materials": MATERIAL_DENSITIES}

@app.get("/materials/categories")
async def get_material_categories():
    return {"categories": list(MATERIAL_DENSITIES.keys())}

@app.get("/material/{material_name}")
async def get_material_density(material_name: str, unit: str = "kg_per_m3"):
    material_data = search_materials(material_name)
    if not material_data:
        raise HTTPException(status_code=404, detail=f"Material '{material_name}' not found")
    material = material_data[0]
    density_kg_m3 = material["density_kg_m3"]
    if unit in CONVERSION_FACTORS["density"]:
        converted_density = density_kg_m3 / CONVERSION_FACTORS["density"][unit]
        return {"material": material["material"], "category": material["category"], "display_name": material["display_name"], "density": converted_density, "unit": unit}
    else:
        raise HTTPException(status_code=400, detail=f"Unit '{unit}' not found")

@app.post("/calculate-mass")
async def calculate_mass(request: MassCalculationRequest):
    material_data = search_materials(request.material)
    if not material_data:
        raise HTTPException(status_code=404, detail=f"Material '{request.material}' not found")
    density_kg_m3 = material_data[0]["density_kg_m3"]
    volume_m3 = request.volume * CONVERSION_FACTORS["volume"][request.volume_unit]
    mass_kg = density_kg_m3 * volume_m3
    mass_result = mass_kg / CONVERSION_FACTORS["mass"][request.mass_unit]
    return {"material": material_data[0]["material"], "density_kg_m3": density_kg_m3, "volume": request.volume, "volume_unit": request.volume_unit, "mass": mass_result, "mass_unit": request.mass_unit, "mass_kg": mass_kg}

@app.get("/calculate-volume")
async def calculate_volume(material: str, mass: float, mass_unit: str = "kilogram", volume_unit: str = "cubic_meter"):
    material_data = search_materials(material)
    if not material_data:
        raise HTTPException(status_code=404, detail=f"Material '{material}' not found")
    density_kg_m3 = material_data[0]["density_kg_m3"]
    mass_kg = mass * CONVERSION_FACTORS["mass"][mass_unit]
    volume_m3 = mass_kg / density_kg_m3
    volume_result = volume_m3 / CONVERSION_FACTORS["volume"][volume_unit]
    return {"material": material_data[0]["material"], "density_kg_m3": density_kg_m3, "mass": mass, "mass_unit": mass_unit, "volume": volume_result, "volume_unit": volume_unit}

@app.get("/search-materials")
async def search_materials_endpoint(query: str, category: Optional[str] = None):
    results = search_materials(query, category)
    return {"query": query, "results": results, "count": len(results)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)