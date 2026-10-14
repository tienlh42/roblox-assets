-- Anime-style effects for the eggs, driven by the model attributes "Rarity", "Anim" and "Progress"
-- (incubation progress from 0 to 1, set by the game; missing means 0). Runs on each client, uses only
-- built-in particle textures (see STYLE_GUIDE.md). The same script serves all six eggs: the spinning halo
-- (Legendary, Mythic) and the swinging bag (Mythic) only run when the egg has those parts.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local egg = script.Parent
local root = egg:WaitForChild("HumanoidRootPart")
local star = egg:WaitForChild("Star")

-- Seconds into Hatch (matches the animation): the shell breaks, the top half lands, the star settles.
local POP_TIME = 2.4
local LAND_TIME = 3.4
local SETTLE_TIME = 3.8
-- Progress at which crack level 1, 2 and 3 appear while incubating, and the seconds into Hatch at which the
-- levels that are not shown yet appear while the egg rocks.
local CRACK_LEVELS = { 0.3, 0.6, 0.9 }
local CRACK_TIMES = { 0.4, 0.9, 1.4 }
local ROOT_HEIGHT = 0.5 -- height of the HumanoidRootPart center above the ground, in the model
local HALO_SPEED = 1.6 -- radians per second
local BAG_SWING = 0.14 -- radians
local BAG_SPEED = 2.2
local WARM_COLOR = Color3.fromRGB(255, 170, 80)
local STAR_COLOR = Color3.fromRGB(242, 194, 48)
local DUST_COLOR = Color3.fromRGB(245, 245, 240)

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 77)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(242, 194, 48)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(92, 214, 107)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(61, 184, 245)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(155, 107, 255)),
})

-- idleRate: sparkles per second while waiting, burst: sparkles when the shell breaks, rays: light beam on break.
local RARITIES = {
	Common = { color = Color3.fromRGB(245, 245, 240), idleRate = 0, burst = 20 },
	Rare = { color = Color3.fromRGB(61, 184, 245), idleRate = 3, burst = 40 },
	Epic = { color = Color3.fromRGB(155, 107, 255), idleRate = 6, burst = 70 },
	Legendary = { color = Color3.fromRGB(242, 194, 48), idleRate = 10, burst = 110, rays = true },
	Mythic = { color = Color3.fromRGB(255, 255, 255), idleRate = 14, burst = 150, rays = true, rainbow = true },
}

local rarity = egg:GetAttribute("Rarity")
local config = assert(RARITIES[rarity], egg.Name .. ": unknown Rarity " .. tostring(rarity))

local outline = Instance.new("Highlight")
outline.FillTransparency = 1
outline.OutlineColor = config.color
outline.DepthMode = Enum.HighlightDepthMode.Occluded
outline.Parent = egg

-- Emitters sit on attachments of the root (y is the height above the model's ground) so their directions
-- stay upright whatever the orientation of the animated parts.
local function attachmentAt(y)
	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(0, y - ROOT_HEIGHT, 0)
	attachment.Parent = root
	return attachment
end

local middle = attachmentAt(1.5)
local top = attachmentAt(3)
local ground = attachmentAt(0.05)

local light = Instance.new("PointLight")
light.Color = config.color
light.Range = 0
light.Parent = middle

local function newEmitter(parent, color, speed, size)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = if config.rainbow and color == config.color then RAINBOW else ColorSequence.new(color)
	emitter.LightEmission = 1
	emitter.Rate = 0
	emitter.Lifetime = NumberRange.new(0.6, 1.2)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, size),
		NumberSequenceKeypoint.new(1, 0),
	})
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-120, 120)
	emitter.Parent = parent
	return emitter
end

local sparkles = newEmitter(middle, config.color, 4, 0.5)
local burst = newEmitter(middle, config.color, 20, 0.6)
local trail = newEmitter(star, STAR_COLOR, 3, 0.4)

local dust = newEmitter(ground, DUST_COLOR, 8, 0.8)
dust.LightEmission = 0
dust.Lifetime = NumberRange.new(0.5, 0.9)
dust.SpreadAngle = Vector2.new(90, 90)
dust.EmissionDirection = Enum.NormalId.Top

-- Warm steam puffing out of the top while incubating.
local steam = newEmitter(top, DUST_COLOR, 2, 0.7)
steam.LightEmission = 0.3
steam.Lifetime = NumberRange.new(1, 1.6)
steam.SpreadAngle = Vector2.new(20, 20)
steam.EmissionDirection = Enum.NormalId.Top
steam.Transparency = NumberSequence.new({
	NumberSequenceKeypoint.new(0, 0.5),
	NumberSequenceKeypoint.new(1, 1),
})

local cracks = {}
for _, part in egg:GetDescendants() do
	local level = if part:IsA("BasePart") then tonumber(part.Name:match("^Crack(%d)_")) else nil
	if level then
		table.insert(cracks, { part = part, level = level })
	end
end

local function showCracks(level)
	for _, crack in cracks do
		if crack.level <= level then
			crack.part.Transparency = 0
		end
	end
end

local function updateCracks()
	if egg:GetAttribute("Anim") == "Hatch" then
		return
	end
	local progress = egg:GetAttribute("Progress") or 0
	for _, crack in cracks do
		crack.part.Transparency = if progress >= CRACK_LEVELS[crack.level] then 0 else 1
	end
end

local function findWeld(partName)
	for _, descendant in egg:GetDescendants() do
		if descendant:IsA("Weld") and descendant.Part1 and descendant.Part1.Name == partName then
			return descendant, descendant.C0
		end
	end
	return nil, nil
end

local haloWeld, haloC0 = findWeld("Halo")
local bagWeld, bagC0 = findWeld("BagHinge")

local function flash(peak)
	light.Color = config.color
	light.Range = peak
	TweenService:Create(light, TweenInfo.new(0.8), { Range = 0 }):Play()
end

local function showRays()
	local ray = Instance.new("Part")
	ray.Anchored = true
	ray.CanCollide = false
	ray.CanQuery = false
	ray.Material = Enum.Material.Neon
	ray.Color = config.color
	ray.Transparency = 0.4
	ray.Size = Vector3.new(0.7, 1, 0.7)
	ray.CFrame = root.CFrame * CFrame.new(0, 2.5, 0)
	ray.Parent = egg
	local goal = {
		Size = Vector3.new(2.2, 24, 2.2),
		CFrame = root.CFrame * CFrame.new(0, 14, 0),
		Transparency = 1,
	}
	local tween = TweenService:Create(ray, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), goal)
	tween.Completed:Once(function()
		ray:Destroy()
	end)
	tween:Play()
end

local function onAnim(name)
	sparkles.Rate = if name == "Idle" then config.idleRate else 0
	steam.Rate = if name == "Incubate" then 3 else 0
	if name ~= "Incubate" then
		light.Range = 0
	end
	updateCracks()

	if name == "Hatch" then
		for level, time in CRACK_TIMES do
			task.delay(time, function()
				if egg:GetAttribute("Anim") == name then
					showCracks(level)
				end
			end)
		end
		task.delay(POP_TIME, function()
			if egg:GetAttribute("Anim") ~= name then
				return
			end
			burst:Emit(config.burst)
			flash(20)
			trail.Rate = 25
			if config.rays then
				showRays()
			end
		end)
		task.delay(LAND_TIME, function()
			if egg:GetAttribute("Anim") == name then
				dust:Emit(14)
			end
		end)
		task.delay(SETTLE_TIME, function()
			trail.Rate = 0
		end)
	else
		trail.Rate = 0
	end
end

egg:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(egg:GetAttribute("Anim"))
end)
egg:GetAttributeChangedSignal("Progress"):Connect(updateCracks)
onAnim(egg:GetAttribute("Anim"))

-- Outline pulses to call attention (Mythic cycles through the rainbow); the warm glow breathes while incubating;
-- the halo (tilted ring) turns around the vertical axis and the bag swings on its string.
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	local anim = egg:GetAttribute("Anim")
	if config.rainbow then
		outline.OutlineColor = Color3.fromHSV(t / 3 % 1, 0.6, 1)
	end
	if anim == "Idle" or anim == "Incubate" then
		outline.OutlineTransparency = 0.5 + 0.4 * math.sin(t * 5)
	end
	if anim == "Incubate" then
		light.Color = WARM_COLOR
		light.Range = 6 + 2 * math.sin(t * 4)
	end
	if haloWeld then
		haloWeld.C0 = CFrame.Angles(0, t * HALO_SPEED, 0) * haloC0
	end
	if bagWeld then
		bagWeld.C0 = bagC0 * CFrame.Angles(0, 0, BAG_SWING * math.sin(t * BAG_SPEED))
	end
end)
