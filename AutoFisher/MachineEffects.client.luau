-- Effects for the fishing machines, driven by the model attributes "Rarity", "Anim", "Slots" (rods plugged in, 1 to 3,
-- missing means 3) and "Fill" (fish in the pouch, 0 to 3, missing means 0). Runs on each client, uses only built-in
-- particle textures (see STYLE_GUIDE.md). The same script serves all five rarities.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local machine = script.Parent
local root = machine:WaitForChild("HumanoidRootPart")
local lamp = machine:WaitForChild("Lamp")

-- Seconds into each animation (matches the animations).
local GULP_TIME = 0.5 -- Catch: the pelican gulps the fish down
local SPIT_TIME = 0.6 -- Collect: the pouch is emptied
local SNEEZE_TIME = 1.4 -- Collect: the atchoo
local ROOT_HEIGHT = 0.5 -- height of the HumanoidRootPart center above the ground, in the model
local HALO_SPEED = 1.6 -- radians per second
local LINE_COLOR = Color3.fromRGB(235, 240, 245)
local STEAM_COLOR = Color3.fromRGB(245, 245, 240)
local LAMP_COLORS = {
	Idle = Color3.fromRGB(255, 200, 50),
	Work = Color3.fromRGB(92, 214, 107),
	Catch = Color3.fromRGB(200, 255, 200),
	Full = Color3.fromRGB(255, 90, 77),
	Collect = Color3.fromRGB(61, 184, 245),
}

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 77)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(242, 194, 48)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(92, 214, 107)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(61, 184, 245)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(155, 107, 255)),
})

-- idleRate: sparkles per second around the body, burst: sparkles when a fish is gulped (doubled when collecting).
local RARITIES = {
	Common = { color = Color3.fromRGB(245, 245, 240), idleRate = 0, burst = 15 },
	Rare = { color = Color3.fromRGB(61, 184, 245), idleRate = 3, burst = 30 },
	Epic = { color = Color3.fromRGB(155, 107, 255), idleRate = 6, burst = 50 },
	Legendary = { color = Color3.fromRGB(242, 194, 48), idleRate = 10, burst = 80 },
	Mythic = { color = Color3.fromRGB(255, 255, 255), idleRate = 14, burst = 110, rainbow = true },
}

local rarity = machine:GetAttribute("Rarity")
local config = assert(RARITIES[rarity], machine.Name .. ": unknown Rarity " .. tostring(rarity))

local outline = Instance.new("Highlight")
outline.FillTransparency = 1
outline.OutlineColor = config.color
outline.DepthMode = Enum.HighlightDepthMode.Occluded
outline.Parent = machine

-- Emitters sit on attachments of the root (y is the height above the model's ground, x and z from its center).
local function attachmentAt(x, y, z)
	local attachment = Instance.new("Attachment")
	attachment.Position = Vector3.new(x, y - ROOT_HEIGHT, z)
	attachment.Parent = root
	return attachment
end

local bodyPoint = attachmentAt(0, 2, 0)
local mouthPoint = attachmentAt(0, 3.7, -3)
local chimneyPoint = attachmentAt(0.8, 3.8, 0.7)

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

local sparkles = newEmitter(bodyPoint, config.color, 4, 0.5)
local burst = newEmitter(mouthPoint, config.color, 14, 0.6)

-- Steam puffing out of the chimney: thin while idle, steady while working, a big puff for the atchoo.
local steam = newEmitter(chimneyPoint, STEAM_COLOR, 2, 0.8)
steam.LightEmission = 0.3
steam.Lifetime = NumberRange.new(1, 1.6)
steam.SpreadAngle = Vector2.new(20, 20)
steam.EmissionDirection = Enum.NormalId.Top
steam.Transparency = NumberSequence.new({
	NumberSequenceKeypoint.new(0, 0.5),
	NumberSequenceKeypoint.new(1, 1),
})

local light = Instance.new("PointLight")
light.Color = config.color
light.Range = 0
light.Parent = mouthPoint

-- One fishing line (a Beam) per rod; a locked slot hides its rod and its line.
local lines = {}
for slot = 1, 3 do
	local tip = machine:FindFirstChild("Rod" .. slot .. "_Tip")
	local lineEnd = machine:FindFirstChild("Rod" .. slot .. "_LineEnd")
	if tip and lineEnd then
		local from = Instance.new("Attachment")
		from.Parent = tip
		local to = Instance.new("Attachment")
		to.Parent = lineEnd
		local beam = Instance.new("Beam")
		beam.Attachment0 = from
		beam.Attachment1 = to
		beam.Width0 = 0.04
		beam.Width1 = 0.04
		beam.FaceCamera = true
		beam.LightEmission = 0.3
		beam.Segments = 8
		beam.Color = if config.rainbow then RAINBOW else ColorSequence.new(LINE_COLOR)
		beam.Parent = tip
		lines[slot] = beam
	end
end

-- Rod parts are named "Rod<slot>_...", the padlock parts "LockCap<slot>" and "LockBody<slot>", the pouch levels
-- "PouchBulge<level>".
local function slotOf(part)
	return tonumber(part.Name:match("^Rod(%d)_") or part.Name:match("^Lock%a+(%d)$"))
end

local function updateSlots()
	local slots = machine:GetAttribute("Slots") or 3
	for _, part in machine:GetDescendants() do
		if part:IsA("BasePart") and not part.Name:match("_LineEnd$") then
			local slot = slotOf(part)
			if slot then
				local isLock = part.Name:match("^Lock") ~= nil
				part.Transparency = if (slot > slots) == isLock then 0 else 1
			end
		end
	end
	for slot, beam in lines do
		beam.Enabled = slot <= slots
	end
end

local function updateFill()
	local fill = machine:GetAttribute("Fill") or 0
	for level = 1, 3 do
		local bulge = machine:FindFirstChild("PouchBulge" .. level)
		if bulge then
			bulge.Transparency = if level <= fill then 0 else 1
		end
	end
end

local halo = nil
for _, descendant in machine:GetDescendants() do
	if descendant:IsA("Weld") and descendant.Part1 and descendant.Part1.Name == "Halo" then
		halo = { weld = descendant, c0 = descendant.C0 }
	end
end

local function flash(peak)
	light.Color = config.color
	light.Range = peak
	TweenService:Create(light, TweenInfo.new(0.6), { Range = 0 }):Play()
end

local function onAnim(name)
	sparkles.Rate = if name == "Idle" or name == "Work" then config.idleRate else 0
	steam.Rate = if name == "Work" then 6 elseif name == "Idle" or name == "Full" then 1 else 0
	lamp.Color = LAMP_COLORS[name] or LAMP_COLORS.Idle

	local function later(time, action)
		task.delay(time, function()
			if machine:GetAttribute("Anim") == name then
				action()
			end
		end)
	end

	if name == "Catch" then
		later(GULP_TIME, function()
			burst:Emit(config.burst)
			flash(10)
		end)
	elseif name == "Collect" then
		later(SPIT_TIME, function()
			burst:Emit(config.burst * 2)
			flash(14)
		end)
		later(SNEEZE_TIME, function()
			steam:Emit(14)
		end)
	end
end

machine:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(machine:GetAttribute("Anim"))
end)
machine:GetAttributeChangedSignal("Slots"):Connect(updateSlots)
machine:GetAttributeChangedSignal("Fill"):Connect(updateFill)
updateSlots()
updateFill()
onAnim(machine:GetAttribute("Anim"))

-- Outline pulses to call attention (Mythic cycles through the rainbow), the lamp blinks when full, the halo turns
-- around the vertical axis.
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	local anim = machine:GetAttribute("Anim")
	if config.rainbow then
		outline.OutlineColor = Color3.fromHSV(t / 3 % 1, 0.6, 1)
	end
	if anim == "Idle" or anim == "Full" then
		outline.OutlineTransparency = 0.5 + 0.4 * math.sin(t * 5)
	end
	if anim == "Full" then
		lamp.Color = if math.sin(t * 8) > 0 then LAMP_COLORS.Full else LAMP_COLORS.Idle
	end
	if halo then
		halo.weld.C0 = CFrame.Angles(0, t * HALO_SPEED, 0) * halo.c0
	end
end)
