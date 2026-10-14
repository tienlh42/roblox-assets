-- Anime-style effects for the treasure chest, driven by the model attributes "Rarity" and "Anim"
-- (see STYLE_GUIDE.md). Runs on each client, uses only built-in particle textures.

local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local chest = script.Parent
local base = chest:WaitForChild("Base")

local RAINBOW = ColorSequence.new({
	ColorSequenceKeypoint.new(0, Color3.fromRGB(255, 90, 77)),
	ColorSequenceKeypoint.new(0.25, Color3.fromRGB(242, 194, 48)),
	ColorSequenceKeypoint.new(0.5, Color3.fromRGB(92, 214, 107)),
	ColorSequenceKeypoint.new(0.75, Color3.fromRGB(61, 184, 245)),
	ColorSequenceKeypoint.new(1, Color3.fromRGB(155, 107, 255)),
})

-- idleRate: sparkles per second while waiting, burst: sparkles when opened, rays: light beam on open.
local RARITIES = {
	Common = { color = Color3.fromRGB(245, 245, 240), idleRate = 0, burst = 12, rays = false },
	Rare = { color = Color3.fromRGB(61, 184, 245), idleRate = 3, burst = 25, rays = false },
	Epic = { color = Color3.fromRGB(155, 107, 255), idleRate = 6, burst = 45, rays = false },
	Legendary = { color = Color3.fromRGB(242, 194, 48), idleRate = 10, burst = 70, rays = true },
	Mythic = { color = Color3.fromRGB(255, 255, 255), idleRate = 14, burst = 100, rays = true, rainbow = true },
}
local SPLASH_COLOR = Color3.fromRGB(61, 184, 245)

local rarity = chest:GetAttribute("Rarity")
local config = assert(RARITIES[rarity], chest.Name .. ": unknown Rarity " .. tostring(rarity))
local size = base.Size

local outline = Instance.new("Highlight")
outline.FillTransparency = 1
outline.OutlineColor = config.color
outline.DepthMode = Enum.HighlightDepthMode.Occluded
outline.Parent = chest

local light = Instance.new("PointLight")
light.Color = config.color
light.Range = 0
light.Parent = base

local function newEmitter(color, rate, speed)
	local emitter = Instance.new("ParticleEmitter")
	emitter.Color = if config.rainbow then RAINBOW else ColorSequence.new(color)
	emitter.LightEmission = 1
	emitter.Rate = rate
	emitter.Lifetime = NumberRange.new(0.6, 1.2)
	emitter.Speed = NumberRange.new(speed * 0.6, speed)
	emitter.SpreadAngle = Vector2.new(180, 180)
	emitter.Size = NumberSequence.new({
		NumberSequenceKeypoint.new(0, 0),
		NumberSequenceKeypoint.new(0.2, size.Y * 0.35),
		NumberSequenceKeypoint.new(1, 0),
	})
	emitter.Rotation = NumberRange.new(0, 360)
	emitter.RotSpeed = NumberRange.new(-120, 120)
	emitter.Parent = base
	return emitter
end

local sparkles = newEmitter(config.color, 0, 4)
local splash = newEmitter(SPLASH_COLOR, 0, 12)
local burst = newEmitter(config.color, 0, 22)

local function flash(peak)
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
	ray.Size = Vector3.new(size.X * 0.3, 1, size.X * 0.3)
	ray.CFrame = base.CFrame * CFrame.new(0, size.Y * 0.5 + 0.5, 0)
	ray.Parent = chest
	local goal = {
		Size = Vector3.new(size.X * 0.9, size.Y * 8, size.X * 0.9),
		CFrame = base.CFrame * CFrame.new(0, size.Y * 4.5, 0),
		Transparency = 1,
	}
	local tween = TweenService:Create(ray, TweenInfo.new(1.2, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), goal)
	tween.Completed:Once(function()
		ray:Destroy()
	end)
	tween:Play()
end

local function fadeOut()
	for _, descendant in chest:GetDescendants() do
		if descendant:IsA("BasePart") and descendant.Transparency < 1 then
			TweenService:Create(descendant, TweenInfo.new(0.5), { Transparency = 1 }):Play()
		end
	end
	TweenService:Create(outline, TweenInfo.new(0.5), { OutlineTransparency = 1 }):Play()
end

local function onAnim(name)
	sparkles.Rate = if name == "Idle" then config.idleRate else 0
	if name == "Spawn" then
		splash:Emit(30)
	elseif name == "Open" then
		task.delay(0.42, function()
			burst:Emit(config.burst)
			flash(12 + size.Y * 4)
			if config.rays then
				showRays()
			end
		end)
	elseif name == "Vanish" then
		task.delay(0.4, function()
			burst:Emit(config.burst * 0.5)
			fadeOut()
		end)
	end
end

chest:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(chest:GetAttribute("Anim"))
end)
onAnim(chest:GetAttribute("Anim"))

-- Outline pulses to call attention; Mythic cycles through the rainbow.
RunService.Heartbeat:Connect(function()
	local t = os.clock()
	if config.rainbow then
		outline.OutlineColor = Color3.fromHSV(t / 3 % 1, 0.6, 1)
	end
	if chest:GetAttribute("Anim") == "Idle" then
		outline.OutlineTransparency = 0.5 + 0.4 * math.sin(t * 5)
	end
end)
