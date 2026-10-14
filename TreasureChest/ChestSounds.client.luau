-- Plays a sound for each chest action, driven by the model attributes "Rarity" and "Anim".
-- Upload the WAV files in Sounds/ to Roblox, then paste the ids below as "rbxassetid://123456".
-- An empty id is skipped, so the chest works silently until the sounds are uploaded.

local IDS = {
	Spawn = "",
	Idle = "",
	Open = "",
	Vanish = "",
	Chime = {
		Common = "",
		Rare = "",
		Epic = "",
		Legendary = "",
		Mythic = "",
	},
}

-- Seconds into Open at which the lid pops (matches the animation).
local LID_POP_TIME = 0.42
local IDLE_PERIOD = 1.4
local VOLUME = { Common = 0.5, Rare = 0.55, Epic = 0.65, Legendary = 0.75, Mythic = 0.8 }

local chest = script.Parent
local base = chest:WaitForChild("Base")
local rarity = chest:GetAttribute("Rarity")

local function play(soundId, volume)
	if soundId == "" then
		return
	end
	local sound = Instance.new("Sound")
	sound.SoundId = soundId
	sound.Volume = volume or VOLUME[rarity]
	sound.RollOffMaxDistance = 80
	sound.Parent = base
	sound.Ended:Once(function()
		sound:Destroy()
	end)
	sound:Play()
end

local idleRun = 0

local function onAnim(name)
	idleRun += 1
	local run = idleRun
	if name == "Idle" then
		task.spawn(function()
			while idleRun == run do
				play(IDS.Idle, 0.4)
				task.wait(IDLE_PERIOD)
			end
		end)
	elseif name == "Open" then
		play(IDS.Open)
		task.delay(LID_POP_TIME, function()
			play(IDS.Chime[rarity])
		end)
	else
		play(IDS[name])
	end
end

chest:GetAttributeChangedSignal("Anim"):Connect(function()
	onAnim(chest:GetAttribute("Anim"))
end)
onAnim(chest:GetAttribute("Anim"))
